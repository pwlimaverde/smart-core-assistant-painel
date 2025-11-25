from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("trello_sync", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trellomember",
            name="external_id",
            field=models.CharField(
                max_length=64, unique=True, blank=True, null=True
            ),
        ),
        migrations.AlterField(
            model_name="trellomember",
            name="username",
            field=models.CharField(max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name="trellomember",
            name="email",
            field=models.EmailField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="trellomember",
            name="is_invited",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="trellomember",
            name="invite_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
