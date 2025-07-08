from django.db import models
from decimal import Decimal
from nepali_datetime import date as bs_date

class Bank(models.Model):
    name = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "बैंक"
        verbose_name_plural = "बैंकहरु"

class Issue(models.Model):
    id = models.CharField(max_length=15, primary_key=True, verbose_name='मुद्दा नम्बर')
    title = models.CharField(max_length=100, null=True, blank=True, verbose_name='शीर्षक')
    petitioner = models.ForeignKey(Bank, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='वादी')
    defendant = models.CharField(max_length=100, null=True, blank=True, verbose_name='प्रतिवादी')

    principal_amount = models.DecimalField(max_digits=20, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    prepaid_amount = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'))

    issue_date_bs = models.CharField(max_length=20, verbose_name="साँवा गणना शुरु (वि.सं)")
    final_date_bs = models.CharField(max_length=20, verbose_name="अन्तिम मिति (वि.सं)")

    total_days = models.IntegerField(blank=True, editable=False, verbose_name="कुल दिन")
    interest_amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, editable=False, verbose_name="ब्याज रकम")
    claimed_amount = models.DecimalField(max_digits=20, decimal_places=2)
    TAX_RATE_CHOICES = [(Decimal('0.010'), '1%'), (Decimal('0.005'), '0.5%')]
    tax_rate = models.DecimalField(max_digits=6, decimal_places=3, choices=TAX_RATE_CHOICES, default=Decimal('0.010'), verbose_name="drt-शुल्क")
    tax_revenue_amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, editable=False, verbose_name="राजस्व रकम")
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, editable=False,  verbose_name='कुल रकम')
    payable_amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, editable=False, verbose_name='भुक्तानी गर्नुपर्ने रकम')

    STATUS_CHOICES = [('open', 'Open'), ('closed', 'Closed'), ('pending', 'Pending')]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Extra fields for saving AD dates converted from BS strings (not editable)
    issue_date = models.DateField(editable=False, null=True, blank=True)
    final_date = models.DateField(editable=False, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Convert BS dates to AD datetime.date objects for calculations
        bs1 = bs_date(*map(int, self.issue_date_bs.split('-')))
        bs2 = bs_date(*map(int, self.final_date_bs.split('-')))
        self.issue_date = bs1.to_datetime_date()
        self.final_date = bs2.to_datetime_date()

        self.total_days = (bs2 - bs1).days

        self.interest_amount = ((self.principal_amount * self.interest_rate * self.total_days) / Decimal('36500')).quantize(Decimal('0.01'))

        self.total_amount = (self.claimed_amount + self.interest_amount).quantize(Decimal('0.01'))
        self.tax_revenue_amount = (self.total_amount * self.tax_rate).quantize(Decimal('0.01'))
        self.payable_amount = (self.tax_revenue_amount - self.prepaid_amount).quantize(Decimal('0.01'))

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or self.id

    class Meta:
        verbose_name = "थप गणना"
        verbose_name_plural = "गणना गर्नु होस"
