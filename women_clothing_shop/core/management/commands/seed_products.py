"""
Django management command to seed product data.

Loads product information from a JSON file and populates the database
with categories, colors, products, variants, and images. Supports
upserting by title and clearing existing data before seeding.
"""
import os
import json
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from shop.models import Category, Color, Clothe, ClotheVariant, ClotheImage


class Command(BaseCommand):
    help = "Seed clothes from data/products.json and copy images into MEDIA_ROOT."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Upsert by title (update if exists).")
        parser.add_argument("--clear", action="store_true", help="Delete all clothes (and related) before seeding.")

    def handle(self, *args, **options):
        force = options["force"]
        clear = options["clear"]

        json_path = Path(settings.BASE_DIR) / "data" / "products.json"
        source_dir = Path(settings.BASE_DIR) / "static" / "clothe_images"
        media_root = Path(settings.MEDIA_ROOT)

        if not json_path.exists():
            self.stdout.write(self.style.ERROR(f"Missing JSON: {json_path}"))
            return

        if not source_dir.is_dir():
            self.stdout.write(self.style.ERROR(f"Missing image source dir: {source_dir}"))
            return

        if clear:
            self.stdout.write(self.style.WARNING("Clearing Clothe data..."))
            Clothe.objects.all().delete()

        data = json.loads(json_path.read_text(encoding="utf-8"))
        products = data.get("products") or []
        if not products:
            self.stdout.write(self.style.WARNING("No products found under key 'products'."))
            return

        created = updated = failed = 0

        for item in products:
            title = (item.get("title") or "").strip()
            if not title:
                failed += 1
                self.stdout.write(self.style.ERROR("Skipping item with empty title."))
                continue

            try:
                with transaction.atomic():
                    category_name = (item.get("category") or "").strip() or "عمومی"
                    category, _ = Category.objects.get_or_create(name=category_name)

                    defaults = {
                        "description": item.get("description") or "",
                        "price": item.get("price") if item.get("price") is not None else 0,
                        "discount_percentage": item.get("discount_percentage") or 0,
                        "category": category,
                    }

                    # Upsert by title
                    if force:
                        clothe, was_created = Clothe.objects.update_or_create(title=title, defaults=defaults)
                    else:
                        clothe, was_created = Clothe.objects.get_or_create(title=title, defaults=defaults)

                    # --- main image copy + set ---
                    image_name = (item.get("image") or "").strip()
                    if image_name:
                        src = source_dir / image_name
                        rel = Path("clothe_images") / image_name
                        dst = media_root / rel

                        if src.exists():
                            dst.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copyfile(src, dst)
                            # Set ImageField to relative path under MEDIA_ROOT
                            clothe.image = str(rel).replace("\\", "/")
                        else:
                            self.stdout.write(self.style.WARNING(f"Missing main image file: {src}"))

                    clothe.save()

                    # --- variants ---
                    variants = item.get("variants") or []
                    if not variants:
                        # Skip products without variants to avoid incomplete data
                        self.stdout.write(self.style.WARNING(f'No variants for "{title}" (skipped variants).'))
                    else:
                        for v in variants:
                            color_obj = v.get("color") or {}
                            color_name = (color_obj.get("name") or "").strip()
                            color_code = (color_obj.get("color_code") or "").strip()

                            size = (v.get("size") or "").strip()
                            stock = v.get("stock") or 0

                            if not (color_name and color_code and size):
                                self.stdout.write(self.style.WARNING(
                                    f'Invalid variant for "{title}" (need color.name, color_code, size). Skipped.'
                                ))
                                continue

                            color, _ = Color.objects.get_or_create(
                                name=color_name,
                                defaults={"color_code": color_code},
                            )
                            # If color exists but color_code differs, update it
                            if color.color_code != color_code:
                                color.color_code = color_code
                                color.save()

                            # Unique constraint: (clothe, color, size)
                            ClotheVariant.objects.update_or_create(
                                clothe=clothe,
                                color=color,
                                size=size,
                                defaults={"stock": stock},
                            )

                    gallery_images = item.get("gallery_images") or []
                    for name in gallery_images:
                        name = (name or "").strip()
                        if not name:
                            continue

                        src = source_dir / "gallery" / name
                        rel = Path("clothe_images") / "gallery" / name
                        dst = media_root / rel

                        if not src.exists():
                            self.stdout.write(self.style.WARNING(f"Gallery image not found, skipping: {src}"))
                            continue

                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(src, dst)

                        ClotheImage.objects.create(
                            clothe=clothe,
                            image=str(rel).replace("\\", "/"),
                        )

                if was_created:
                    created += 1
                else:
                    updated += 1

            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f'Failed "{title}": {e}'))

        self.stdout.write(self.style.SUCCESS(f"Done. created={created}, updated={updated}, failed={failed}"))
