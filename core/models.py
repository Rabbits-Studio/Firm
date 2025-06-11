from decimal import Decimal
from django.db import models

class Bank(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Issue(models.Model):
    id = models.CharField(max_length=15, primary_key=True, verbose_name='मुद्दा नम्बर')
    title = models.CharField(max_length=100)
    petitioner = models.ForeignKey(Bank, on_delete=models.SET_NULL, null=True, blank=True)
    defendant = models.CharField(max_length=100)

    principal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    prepaid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    issue_date = models.DateField()
    final_date = models.DateField()

    total_days = models.IntegerField(blank=True, editable=False)
    interest_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, editable=False)
    claimed_amount = models.DecimalField(max_digits=10, decimal_places=2)

    TAX_RATE_CHOICES = [
        (Decimal('0.01'), '1%'),
        (Decimal('0.005'), '0.5%'),
    ]
    tax_rate = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        choices=TAX_RATE_CHOICES,
        default=Decimal('0.01'),
        verbose_name="Tax Rate"
    )

    tax_revenue_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, editable=False)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, editable=False)
    payable_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, editable=False)

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('pending', 'Pending'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.id:
            raise ValueError("मुद्दा नम्बर (ID) manually specify गर्नुहोस्।")

        self.total_days = (self.final_date - self.issue_date).days

        self.interest_amount = (
            (self.principal_amount * self.interest_rate * self.total_days) / Decimal('36500')
        ).quantize(Decimal('0.01'))

        self.total_amount = (self.claimed_amount + self.interest_amount).quantize(Decimal('0.01'))

        self.tax_revenue_amount = (self.total_amount * self.tax_rate).quantize(Decimal('0.01'))

        self.payable_amount = (self.tax_revenue_amount - self.prepaid_amount).quantize(Decimal('0.01'))

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
