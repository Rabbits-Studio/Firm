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

from nepali_datetime import date as nepali_date

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

    tax_rate = forms.ChoiceField(choices=TAX_CHOICES, label='कर', initial='0.01')
    id = forms.CharField(label='मुद्दा नम्बर', required=False)
    title = forms.CharField(label='शीर्षक', required=False, widget=NepaliUnicodeTextInput())
    defendant = forms.CharField(label='प्रतिवादी', required=False, widget=NepaliUnicodeTextInput())

    principal_amount = forms.CharField(label='सावा रकम')
    claimed_amount = forms.CharField(label='दाबी गरिएको रकम')
    interest_rate = forms.CharField(label='ब्याज दर')
    prepaid_amount = forms.CharField(label='अगावै तिरेको रकम', required=False)

    document_date_bs = forms.CharField(
        label="गणना गरेको मिति (वि.सं)", required=False, widget=NepaliDatePickerWidget()
    )

    class Meta:
        model = Issue
        exclude = ['issue_date', 'final_date']
        widgets = {
            'title': NepaliUnicodeTextInput(),
            'defendant': NepaliUnicodeTextInput(),
            'issue_date_bs': NepaliDatePickerWidget(),
            'final_date_bs': NepaliDatePickerWidget(),
            'document_date_bs': NepaliDatePickerWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = nepali_date.today().strftime('%Y-%m-%d')

        # Set default values on date fields to today if not already set
        for field in ['issue_date_bs', 'final_date_bs', 'document_date_bs']:
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
        'document_date_bs',
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


    def print_pdf_button(self, obj):
        return format_html('<a class="button" href="{}">Print PDF</a>', f"{obj.id}/print_pdf/")
    print_pdf_button.short_description = 'Print PDF'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:issue_id>/print_pdf/', self.admin_site.admin_view(self.print_pdf), name='core_issue_print_pdf'),
        ]
        return custom_urls + urls

    def print_pdf(self, request, issue_id):
        issue = get_object_or_404(self.model, id=issue_id)
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=(595.27, 841.89))  # A4 size points
        p.setTitle(f"मुद्दा विवरण- {issue.id}")

        nepali_font = "NotoDevanagari"
        english_font = "Helvetica"
        font_size = 12

        # Header
        p.setFont(nepali_font, 16)
        p.drawCentredString(297.64, 800, "ऋण असुली न्यायाधिकरण")
        p.drawCentredString(297.64, 775, "राजस्व रकम दाखिला")

        # Date in Nepali numerals
        draw_mixed_text(p, 440, 750, f"मिति: ", nepali_font, english_font, font_size)
        p.rect(470, 745, 90, 20)

        # Layout settings
        y, line_height = 710, 30
        label_x, value_x = 60, 190
        label2_x, value2_x = 320, 440
        box_width, box_height = 110, 20

        pairs = [
            ("मुद्दा नम्बर", str(issue.id)),
            ("वादी", str(issue.petitioner) if issue.petitioner else ""),
            ("प्रतिवादी", issue.defendant or ""),
            ("सावा रकम", convert_to_nepali_number(round(issue.principal_amount, 2)),
             "दाबी रकम", convert_to_nepali_number(round(issue.claimed_amount, 2))),
            ("साँवा गणना शुरु", convert_to_nepali_number(issue.issue_date_bs or ""), "अन्तिम मिति", convert_to_nepali_number(issue.final_date_bs or "")),
            ("कुल दिन", convert_to_nepali_number(issue.total_days or 0)),
            ("ब्याज दर", convert_to_nepali_number(round(issue.interest_rate, 2)) + "%",
             "ब्याज रकम", convert_to_nepali_number(round(issue.interest_amount, 2))),
            ("कुल रकम", convert_to_nepali_number(round(issue.total_amount, 2))),
            ("कर", f"{float(issue.tax_rate)*100:.1f}%",
             "राजस्व रकम", convert_to_nepali_number(round(issue.tax_revenue_amount, 2))),
            ("अगावै तिरेको रकम", convert_to_nepali_number(round(issue.prepaid_amount, 2))),
            ("भुक्तानी गर्नुपर्ने रकम", convert_to_nepali_number(round(issue.payable_amount, 2))),
        ]

        for pair in pairs:
            if len(pair) == 2:
                label, val = pair
                draw_mixed_text(p, label_x, y, f"{label} :", nepali_font, english_font, font_size)
                p.rect(value_x, y - 5, 300 if label == "वादी" else box_width, box_height)
                draw_mixed_text(p, value_x + 5, y + 1, str(val), nepali_font, english_font, font_size)
            else:
                l_label, l_val, r_label, r_val = pair
                draw_mixed_text(p, label_x, y, f"{l_label} :", nepali_font, english_font, font_size)
                p.rect(value_x, y - 5, box_width, box_height)
                draw_mixed_text(p, value_x + 5, y + 1, str(l_val), nepali_font, english_font, font_size)

                draw_mixed_text(p, label2_x, y, f"{r_label} :", nepali_font, english_font, font_size)
                p.rect(value2_x, y - 5, box_width, box_height)
                draw_mixed_text(p, value2_x + 5, y + 1, str(r_val), nepali_font, english_font, font_size)

            y -= line_height
            if y < 100:
                p.showPage()
                p.setFont(nepali_font, font_size)
                y = 800

        p.showPage()
        p.save()
        buffer.seek(0)
        return HttpResponse(
            buffer,
            content_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="mudda_{issue.id}_report.pdf"'}
        )