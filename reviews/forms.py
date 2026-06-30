"""
Forms for review management in the Hop & Barley online store.

This module provides forms for:
- Creating product reviews with rating and comment
"""
from django import forms
from reviews.models import Review


class ReviewForm(forms.ModelForm):
    """
    Form for creating product reviews.

    Collects rating (1-5 stars) and comment from the user.
    Uses radio buttons for rating selection and textarea for comment.

    Attributes:
        model: Review model class.
        fields: List of fields to include in the form.
        widgets: Custom widget configurations.
        labels: Custom field labels.

    Examples:
        >>> form = ReviewForm(data={
        ...     'rating': 5,
        ...     'comment': 'Excellent product!'
        ... })
        >>> form.is_valid()
        True
    """
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        required = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write your review here...'}),
        }
        labels = {
            'rating': 'Rating:',
            'comment': 'Your review:',
        }
