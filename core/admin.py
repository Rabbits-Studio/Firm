import io
import os
import re
import uuid
from decimal import Decimal

from django import forms
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import path
from django.utils.html import format_html

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import white, black
from weasyprint import HTML
from nepali_datetime import date as nepali_date
from django.utils.html import format_html
from django.template.loader import render_to_string
from .models import Issue, Bank
from .widgets import NepaliDatePickerWidget, NepaliUnicodeTextInput


# Admin site titles in Nepali
admin.site.site_title = "ऋण असुली न्यायाधिकरण"
admin.site.index_title = "राजस्व रकम दाखिला"


# Register Devanagari font for PDF generation
font_path = os.path.join(settings.BASE_DIR, "staticfiles/fonts/Kalimati.ttf")
pdfmetrics.registerFont(TTFont("NotoDevanagari", font_path))


# Bank Admin for searchable bank names
@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    search_fields = ['name']


# Utility: Convert English digits to Nepali digits
def convert_to_nepali_number(num):
    nepali_digits = "०१२३४५६७८९"
    try:
        return ''.join(nepali_digits[int(d)] if d.isdigit() else d for d in str(num))
    except Exception:
        return str(num)


# Utility: Generate unique issue ID
def generate_issue_id():
    return f"MU{uuid.uuid4().hex[:6].upper()}"


# Utility: Draw mixed Nepali and English text on PDF canvas
def draw_mixed_text(p, x, y, text, nepali_font, english_font, font_size=12):
    pattern = re.compile(r'([\u0900-\u097F]+|[^\u0900-\u097F]+)')
    chunks = pattern.findall(text or '')
    cursor_x = x
    for chunk in chunks:
        font = nepali_font if re.match(r'^[\u0900-\u097F]+$', chunk) else english_font
        p.setFont(font, font_size)
        p.drawString(cursor_x, y, chunk)
        width = pdfmetrics.stringWidth(chunk, font, font_size)
        cursor_x += width


# Custom admin form for Issue model with Nepali widgets and decimal conversion
class IssueAdminForm(forms.ModelForm):
    TAX_CHOICES = [('0.01', '1%'), ('0.005', '0.5%')]

    tax_rate = forms.ChoiceField(choices=TAX_CHOICES, label='drt-शुल्क', initial='0.01')
    id = forms.CharField(label='मुद्दा नम्बर', required=False)
    title = forms.CharField(label='शीर्षक', required=False, widget=NepaliUnicodeTextInput())
    defendant = forms.CharField(label='प्रतिवादी', required=False, widget=NepaliUnicodeTextInput())

    principal_amount = forms.CharField(label='सावा रकम')
    claimed_amount = forms.CharField(label='दाबी गरिएको रकम')
    interest_rate = forms.CharField(label='ब्याज दर')
    prepaid_amount = forms.CharField(label='अगावै तिरेको रकम', required=False)

    # document_date_bs = forms.CharField(
    #     label="गणना गरेको मिति (वि.सं)", required=False, widget=NepaliDatePickerWidget()
    # )

    class Meta:
        model = Issue
        exclude = ['issue_date', 'final_date']
        widgets = {
            'title': NepaliUnicodeTextInput(),
            'defendant': NepaliUnicodeTextInput(),
            'issue_date_bs': NepaliDatePickerWidget(),
            'final_date_bs': NepaliDatePickerWidget(),
            # 'document_date_bs': NepaliDatePickerWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = nepali_date.today().strftime('%Y-%m-%d')

        # Set default values on date fields to today if not already set
        for field in ['issue_date_bs', 'final_date_bs']: 
        # 'document_date_bs']:
            self.fields[field].widget.attrs.update({
                'value': self.initial.get(field, today)
            })

    def _convert_nepali_to_decimal(self, field):
        val = self.cleaned_data.get(field, "")
        nepali_digits = "०१२३४५६७८९"
        english_digits = "0123456789"
        converted = []

        for ch in val:
            if ch in nepali_digits:
                converted.append(str(nepali_digits.index(ch)))
            elif ch in english_digits or ch == '.':
                converted.append(ch)

        cleaned_val = ''.join(converted)
        return Decimal(cleaned_val) if cleaned_val else Decimal('0.00')

    # Clean methods to convert Nepali digits to Decimal
    def clean_principal_amount(self):
        return self._convert_nepali_to_decimal('principal_amount')

    def clean_claimed_amount(self):
        return self._convert_nepali_to_decimal('claimed_amount')

    def clean_interest_rate(self):
        return self._convert_nepali_to_decimal('interest_rate')

    def clean_prepaid_amount(self):
        return self._convert_nepali_to_decimal('prepaid_amount')

    def clean_tax_rate(self):
        return Decimal(self.cleaned_data['tax_rate'])

    def clean_id(self):
        return self.cleaned_data.get('id', '')


# Issue admin interface
@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    form = IssueAdminForm
    autocomplete_fields = ['petitioner']
    ordering = ['-created_at']

    readonly_fields = [
        'total_days', 'interest_amount', 'tax_revenue_amount',
        'total_amount', 'payable_amount', 'created_at', 'updated_at',
    ]

    fields = [
        'id', 'title', 'petitioner', 'defendant',
        'principal_amount', 'claimed_amount', 'interest_rate',
        'issue_date_bs', 'final_date_bs',
        # 'document_date_bs',
        'total_days', 'interest_amount', 'total_amount', 'tax_rate',
        'tax_revenue_amount', 'prepaid_amount', 'payable_amount', 'status'
    ]

    list_display = (
        'id_nepali', 'title', 'petitioner', 'defendant',
        'total_days', 'interest_amount', 'print_pdf_button'
    )
    def id_nepali(self, obj):
        id_str = str(obj.id)

        # Check if the ID is purely numeric (English digits)
        if id_str.isdigit():
            return convert_to_nepali_number(id_str)

        # If it's mixed (like MU1234 or मुद्दा567), convert only the digits
        nepali_digits = "०१२३४५६७८९"
        return ''.join(
            nepali_digits[int(ch)] if ch.isdigit() else ch
            for ch in id_str
        )
    id_nepali.short_description = 'मुद्दा नम्बर'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:issue_id>/print_pdf/',
                self.admin_site.admin_view(self.print_template_pdf),
                name='issue_print_pdf'
            ),
        ]
        return custom_urls + urls


    def print_pdf_button(self, obj):
        return format_html(
            '<a class="button" target="_blank" href="{}">Print PDF</a>',
            f"{obj.id}/print_pdf/"
        )
    print_pdf_button.short_description = 'Print PDF'

    def print_template_pdf(self, request, issue_id):
        issue = get_object_or_404(Issue, pk=issue_id)

        html_string = render_to_string("issue_pdf.html", {
            "issue": issue,
            "font_url": request.build_absolute_uri("/staticfiles/fonts/NotoSansDevanagari-Regular.ttf")
        })

        pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

        return HttpResponse(
            pdf_file,
            content_type='application/pdf',
            headers={'Content-Disposition': f'inline; filename="mudda_{issue.id}.pdf"'}
        )


    