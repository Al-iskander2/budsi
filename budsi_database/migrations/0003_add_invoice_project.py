from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("budsi_database", "0002_invoice_credit_note_reason_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="project",
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]