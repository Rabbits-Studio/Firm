import nepali_datetime
from django import forms
from decimal import Decimal
from .models import Issue
from .utils.nepali_numerals import eng_to_nep, nep_to_eng
from .widgets import NepaliUnicodeTextInput


class NepaliUnicodeDecimalField(forms.CharField):
    def to_python(self, value):
        if value:
            try:
                english = nep_to_eng(value.strip())
                return Decimal(english)
            except Exception:
                raise forms.ValidationError("कृपया नेपाली अंकमा मात्र संख्या लेख्नुहोस्।")
        return Decimal('0')


class IssueForm(forms.ModelForm):
    issue_date_bs = forms.CharField(
        required=True, label='मुद्दा दर्ता मिति (वि.सं)',
        widget=NepaliUnicodeTextInput()
    )
    final_date_bs = forms.CharField(
        required=True, label='अन्तिम मिति (वि.सं)',
        widget=NepaliUnicodeTextInput()
    )

    principal_amount = NepaliUnicodeDecimalField(
        required=True, label='सावा रकम', widget=NepaliUnicodeTextInput()
    )
    interest_rate = NepaliUnicodeDecimalField(
        required=True, label='ब्याज दर (%)', widget=NepaliUnicodeTextInput()
    )
    prepaid_amount = NepaliUnicodeDecimalField(
        required=False, label='अगावै तिरेको रकम', widget=NepaliUnicodeTextInput()
    )

    class Meta:
        model = Issue
        exclude = [
            'issue_date', 'final_date', 'total_days', 'interest_amount',
            'claimed_amount', 'total_amount', 'payable_amount',
            'tax_revenue_amount', 'id'
        ]

    def clean(self):
        cleaned_data = super().clean()

        issue_date_bs = cleaned_data.get('issue_date_bs')
        final_date_bs = cleaned_data.get('final_date_bs')

        try:
            issue_date = nepali_datetime.date.from_string(issue_date_bs).to_datetime_date()
            final_date = nepali_datetime.date.from_string(final_date_bs).to_datetime_date()
        except Exception as e:
            raise forms.ValidationError(f"मिति त्रुटि : {e}")

        if issue_date > final_date:
            raise forms.ValidationError("मुद्दा दर्ता मिति अन्तिम मितिभन्दा अघि हुनुपर्छ।")

        cleaned_data['issue_date'] = issue_date
        cleaned_data['final_date'] = final_date

        # Calculations
        principal = cleaned_data.get('principal_amount', Decimal('0'))
        interest_rate = cleaned_data.get('interest_rate', Decimal('0'))
        prepaid = cleaned_data.get('prepaid_amount', Decimal('0'))

        total_days = (final_date - issue_date).days
        interest_amount = (principal * interest_rate * total_days) / Decimal('36500')
        claimed_amount = principal + interest_amount
        tax_revenue = claimed_amount * Decimal('0.015')
        total_amount = claimed_amount
        payable_amount = total_amount - prepaid

        # Assign calculated fields
        cleaned_data['total_days'] = total_days
        cleaned_data['interest_amount'] = interest_amount.quantize(Decimal('0.01'))
        cleaned_data['claimed_amount'] = claimed_amount.quantize(Decimal('0.01'))
        cleaned_data['tax_revenue_amount'] = tax_revenue.quantize(Decimal('0.01'))
        cleaned_data['total_amount'] = total_amount.quantize(Decimal('0.01'))
        cleaned_data['payable_amount'] = payable_amount.quantize(Decimal('0.01'))

        return cleaned_data
