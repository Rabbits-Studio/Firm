import io
import os
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.contrib import admin
from django import forms
from django.urls import path
from django.http import HttpResponse
from django.utils.html import format_html
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .models import Issue, Bank
from .widgets import NepaliDatePickerWidget

# Register the Bank model
admin.site.register(Bank)

# Register a Unicode-compatible Nepali font
font_path = os.path.join(settings.BASE_DIR, "staticfiles/fonts/NotoSansDevanagari-Regular.ttf")
pdfmetrics.registerFont(TTFont("NotoDevanagari", font_path))


class IssueAdminForm(forms.ModelForm):
    TAX_CHOICES = [
        (Decimal('0.01'), '1%'),
        (Decimal('0.005'), '0.5%'),
    ]

    tax_rate = forms.ChoiceField(
        choices=TAX_CHOICES,
        label='कर',
        initial=Decimal('0.01')
    )

    class Meta:
        model = Issue
        exclude = []
        labels = {
            'id': 'मुद्दा नम्बर',
            'title': 'शीर्षक',
            'petitioner': 'वादी',
            'defendant': 'प्रतिवादी',
            'principal_amount': 'सावा रकम',
            'interest_rate': 'ब्याज दर',
            'issue_date': 'मुद्दा दर्ता मिति',
            'final_date': 'अन्तिम मिति',
            'total_days': 'कुल दिन',
            'interest_amount': 'ब्याज रकम',
            'claimed_amount': 'दाबी गरिएको रकम',
            'tax_rate': 'कर',
            'tax_revenue_amount': 'राजस्व रकम',
            'total_amount': 'कुल रकम',
            'prepaid_amount': 'अगावै तिरेको रकम',
            'payable_amount': 'भुक्तानी गर्नुपर्ने रकम',
            'status': 'स्थिति',
        }
        widgets = {
            'issue_date': NepaliDatePickerWidget(attrs={'value': date.today().isoformat()}),
            'final_date': NepaliDatePickerWidget(),
        }


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    form = IssueAdminForm

    readonly_fields = [
        'total_days', 'interest_amount',
        'tax_revenue_amount', 'total_amount', 'payable_amount'
    ]

    fields = [
        'id', 'title', 'petitioner', 'defendant', 'principal_amount',
        'claimed_amount', 'interest_rate', 'issue_date', 'final_date',
        'total_days', 'interest_amount', 'total_amount', 'tax_rate',
        'tax_revenue_amount', 'prepaid_amount', 'payable_amount', 'status'
    ]

    list_display = ('id', 'title', 'petitioner', 'defendant', 'print_pdf_button')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:issue_id>/print_pdf/', self.admin_site.admin_view(self.print_pdf), name='core_issue_print_pdf'),
        ]
        return custom_urls + urls

    def print_pdf_button(self, obj):
        return format_html('<a class="button" href="{}">Print PDF</a>', f"{obj.id}/print_pdf/")
    print_pdf_button.short_description = 'Print PDF'

    def print_pdf(self, request, issue_id):
        issue = self.model.objects.filter(id=issue_id).first()
        if not issue:
            return HttpResponse(f"Issue with ID {issue_id} not found.", status=404)

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=(595.27, 841.89))  # A4
        p.setTitle(f"मुद्दा विवरण - {issue.id}")
        p.setFont("NotoDevanagari", 16)

        y = 800
        line_height = 26
        left_margin = 60

        # Title
        p.drawCentredString(297.64, y, "मुद्दा विवरण रिपोर्ट")
        y -= line_height * 2

        fields = [
            ("मुद्दा आईडी", issue.id),
            ("शीर्षक", issue.title),
            ("वादी", str(issue.petitioner)),
            ("प्रतिवादी", issue.defendant),
            ("सावा रकम", f"Rs. {issue.principal_amount}"),
            ("ब्याज दर", f"{issue.interest_rate}%"),
            ("दाबी गरिएको रकम", f"Rs. {issue.claimed_amount}"),
            ("मुद्दा दर्ता मिति", issue.issue_date.strftime("%Y-%m-%d")),
            ("अन्तिम मिति", issue.final_date.strftime("%Y-%m-%d")),
            ("कुल दिन", issue.total_days),
            ("ब्याज रकम", f"Rs. {issue.interest_amount}"),
            ("राजस्व रकम", f"Rs. {issue.tax_revenue_amount}"),
            ("कुल रकम", f"Rs. {issue.total_amount}"),
            ("अगावै तिरेको रकम", f"Rs. {issue.prepaid_amount}"),
            ("भुक्तानी गर्नुपर्ने रकम", f"Rs. {issue.payable_amount}"),
            ("स्थिति", issue.get_status_display()),
        ]

        for label, value in fields:
            p.drawString(left_margin, y, f"{label}: {value}")
            y -= line_height
            if y < 80:
                p.showPage()
                p.setFont("NotoDevanagari", 16)
                y = 800

        p.showPage()
        p.save()
        buffer.seek(0)

        return HttpResponse(buffer, content_type='application/pdf', headers={
            'Content-Disposition': f'attachment; filename="{issue.id}_report.pdf"',
        })
