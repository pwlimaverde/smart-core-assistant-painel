from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clickup_sync", "0002_clickupstatus"),
    ]

    operations = [
        migrations.CreateModel(
            name="ClickupFolder",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("departamento_id", models.BigIntegerField()),
                (
                    "external_id",
                    models.CharField(max_length=128, unique=True),
                ),
                ("name", models.CharField(max_length=128)),
                ("space_external_id", models.CharField(max_length=128)),
            ],
            options={
                "verbose_name": "ClickUp Folder",
                "verbose_name_plural": "ClickUp Folders",
            },
        ),
    ]