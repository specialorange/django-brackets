"""Provides fixture for django-brackets testing."""
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

import pytest
from django import forms
from django.http import HttpResponse
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import BaseFormView, ModelFormMixin
from django.views.generic.list import MultipleObjectMixin

from .project.models import Article

if TYPE_CHECKING:
    from typing import Callable, Type

    from django.db import models

    K = dict


@pytest.mark.django_db()
@pytest.fixture()
def user(django_user_model) -> Callable:
    """Provide a generic user fixture for tests."""

    def _user(**kwargs: K) -> models.Model:
        """Generate a customizable user."""
        defaults: K = {"username": "test", "password": "Test1234"}
        defaults.update(kwargs)
        user: models.Model = django_user_model.objects.create(**defaults)
        return user

    return _user


@pytest.fixture(name="mixin_view")
def mixin_view_factory(request: pytest.FixtureRequest) -> Callable:
    """Combine a mixin and View for a test."""
    mixin_request = request.node.get_closest_marker("mixin")
    if not mixin_request:
        pytest.fail("No mixin marker found")
    mixins = import_module(".mixins", "brackets")
    mixin_name = mixin_request.args[0]
    mixin_class = getattr(mixins, mixin_name)

    def mixin_view(**kwargs: dict) -> Type[View]:
        """Mixed-in view generator."""
        default_functions: dict = {
            "get": lambda s, r: HttpResponse("django-brackets")
        }
        kwargs.update(**default_functions)
        _name = f"{mixin_class.__name__}FixtureView"
        return type(_name, (mixin_class, View), kwargs)

    return mixin_view


@pytest.fixture()
def single_object_view(mixin_view: Callable) -> Callable:
    """Fixture for a view with the `SingleObjectMixin`."""

    def _view(**kwargs: K) -> Type[SingleObjectMixin]:
        """Return a mixin view with the `SingleObjectMixin`."""
        return type(
            "SingleObjectView",
            (mixin_view(), SingleObjectMixin),
            {"model": Article},
            **kwargs,
        )

    return _view


@pytest.fixture()
def multiple_object_view(mixin_view: Callable) -> Callable:
    """Fixture for a view with the `MultipleObjectMixin`."""

    def _view(**kwargs: K) -> Type[MultipleObjectMixin]:
        """Return a mixin view with the `MultipleObjectMixin`."""
        return type(
            "MultipleObjectView",
            (mixin_view(), MultipleObjectMixin),
            {"model": Article},
            **kwargs,
        )

    return _view


@pytest.fixture()
def form_view(mixin_view: Callable) -> Callable:
    """Fixture for a view with the `FormMixin`."""

    def _view(**kwargs: K) -> Type[BaseFormView]:
        """Return a view with the `FormMixin` mixin."""
        return type(
            "FormView",
            (mixin_view(), BaseFormView),
            {
                "http_method_names": ["get", "post"],
                # "post": lambda s, r, *a, **k: HttpResponse("post"),
            },
            **kwargs,
        )

    return _view


@pytest.fixture()
def model_form_view(mixin_view: Callable) -> Callable:
    """Fixture for a view with the `ModelFormMixin`."""

    def _view(**kwargs: K) -> Type[ModelFormMixin]:
        """Return a view with the `ModelFormMixin` mixin."""
        return type(
            "FormView",
            (mixin_view(), ModelFormMixin),
            {
                "model": Article,
                "object": None,
                "http_method_names": ["get", "post"],
                "post": lambda s, r, *a, **k: HttpResponse("post"),
            },
            **kwargs,
        )

    return _view


@pytest.fixture()
def form_class() -> Callable:
    """Generate a new form class with given kwargs."""

    def _form(**kwargs: K) -> Type[forms.Form]:
        """Return a new form class."""

        class MixinForm(forms.Form):
            class Meta:
                fields = "__all__"

        for k, v in kwargs.items():
            setattr(MixinForm, k, v)
        return MixinForm

    return _form


@pytest.fixture()
def model_form_class() -> Callable:
    """Generate a new model form class with given kwargs."""

    def _form(**kwargs: K) -> Type[forms.ModelForm]:
        """Return a new model form class."""

        class MixinModelForm(forms.ModelForm):
            class Meta:
                fields = [k for k in kwargs]
                model = Article

        for k, v in kwargs.items():
            setattr(MixinModelForm, k, v)
        return MixinModelForm

    return _form
