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

from django.shortcuts import get_object_or_404

admin.site.site_title = ("ऋण असुली न्यायाधिकरण")
admin.site.index_title = ("Welcome to राजस्व रकम दाखिला")


admin.site.register(Bank)

font_path = os.path.join(settings.BASE_DIR, "staticfiles/fonts/Kalimati.ttf")
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
        exclude = ['issue_date', 'final_date']
        labels = {
            # 'issue_date_bs': 'मुद्दा दर्ता मिति (वि.सं)',
            # 'final_date_bs': 'अन्तिम मिति (वि.सं)',
            'id': 'मुद्दा नम्बर',
            'title': 'शीर्षक',
            'petitioner': 'वादी',
            'defendant': 'प्रतिवादी',
            'principal_amount': 'सावा रकम',
            'interest_rate': 'ब्याज दर',
            'issue_date_bs': 'मुद्दा दर्ता मिति (वि.सं)',
            'final_date_bs': 'अन्तिम मिति (वि.सं)',
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
            'issue_date_bs': NepaliDatePickerWidget(attrs={'value': date.today().isoformat()}),
            'final_date_bs': NepaliDatePickerWidget(attrs={'value': date.today().isoformat()}),
        }


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    form = IssueAdminForm

    readonly_fields = [
        'issue_date', 'final_date',
        'total_days', 'interest_amount',
        'tax_revenue_amount', 'total_amount', 'payable_amount'
    ]

    fields = [
        'id', 'title', 'petitioner', 'defendant',
        'principal_amount', 'claimed_amount', 'interest_rate',
        'issue_date_bs', 'final_date_bs',
        'issue_date', 'final_date',
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
        issue = get_object_or_404(self.model, id=issue_id)

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=(595.27, 841.89))  # A4
        p.setTitle(f"मुद्दा विवरण- {issue.id}")

        # Register font
        p.setFont("NotoDevanagari", 16)
        p.setLineWidth(1.2)
        p.setFillColorRGB(0, 0, 0)

        # Title
        title_y = 800
        p.drawCentredString(297.64, title_y, "ऋण असुली न्यायाधिकरण")
        p.drawCentredString(297.64, title_y - 25, "राजस्व रकम दाखिला")

        # Date
        p.setFont("NotoDevanagari", 12)
        p.drawRightString(540, title_y - 50, f"मिति: {date.today().strftime('%Y-%m-%d')}")

        # Layout variables
        y = title_y - 90
        line_height = 30
        label_x = 60
        value_x = 170
        label_x2 = 320
        value_x2 = 440
        box_width = 110
        box_height = 20

        # Data pairs
        pairs = [
            ("वादी", str(issue.petitioner)),
            ("प्रतिवादी", issue.defendant),
            ("सावा रकम", f"Rs. {issue.principal_amount}", "दाबी रकम", f"Rs. {issue.claimed_amount}"),
            ("मुद्दा दर्ता मिति", issue.issue_date.strftime("%Y-%m-%d"), "अन्तिम मिति", issue.final_date.strftime("%Y-%m-%d")),
            ("कुल दिन", str(issue.total_days)),
            ("ब्याज दर", f"{issue.interest_rate}%", "ब्याज रकम", f"Rs. {issue.interest_amount}"),
            ("कुल रकम", f"Rs. {issue.total_amount}"),
            ("कर", f"{float(issue.tax_rate) * 100:.1f}%", "राजस्व रकम", f"Rs. {issue.tax_revenue_amount}"),
            ("अगावै तिरेको रकम", f"Rs. {issue.prepaid_amount}"),
            ("भुक्तानी गर्नुपर्ने रकम", f"Rs. {issue.payable_amount}"),
        ]

        for pair in pairs:
            if len(pair) == 2:
                label, val = pair
                p.drawString(label_x, y, f"{label} :")
                if label == "वादी":
                    # Border only around value
                    p.rect(value_x, y - 5, 300, box_height)
                    p.drawString(value_x + 5, y + 1, str(val))
                else:
                    p.rect(value_x, y - 5, box_width, box_height)
                    p.drawString(value_x + 5, y + 1, str(val))
            elif len(pair) == 4:
                left_label, left_val, right_label, right_val = pair
                # Left side
                p.drawString(label_x, y, f"{left_label} :")
                p.rect(value_x, y - 5, box_width, box_height)
                p.drawString(value_x + 5, y + 1, str(left_val))
                # Right side
                p.drawString(label_x2, y, f"{right_label} :")
                p.rect(value_x2, y - 5, box_width, box_height)
                p.drawString(value_x2 + 5, y + 1, str(right_val))

            y -= line_height

            # Page break if needed
            if y < 100:
                p.showPage()
                p.setFont("NotoDevanagari", 12)
                y = 800

        p.showPage()
        p.save()
        buffer.seek(0)

        return HttpResponse(buffer, content_type='application/pdf', headers={
            'Content-Disposition': f'attachment; filename="{issue.id}_report.pdf"',
        })
