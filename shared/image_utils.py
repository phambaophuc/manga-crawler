from io import BytesIO
import logging
from typing import Optional, Tuple
from PIL import Image

logger = logging.getLogger(__name__)


class ImageConverter:
    DEFAULT_WEBP_QUALITY = 85
    DEFAULT_JPEG_QUALITY = 90
    MAX_WEBP_SIZE = 16383

    @staticmethod
    def to_webp(
        image_data: bytes, quality: int = DEFAULT_WEBP_QUALITY
    ) -> Tuple[Optional[bytes], int]:

        try:
            image = Image.open(BytesIO(image_data))

            if (
                image.width > ImageConverter.MAX_WEBP_SIZE
                or image.height > ImageConverter.MAX_WEBP_SIZE
            ):
                logger.warning(
                    f"Image size {image.size} exceeds WebP limit ({ImageConverter.MAX_WEBP_SIZE}px). Resizing..."
                )
                resized_data, _ = ImageConverter.resize_image(
                    image_data,
                    max_width=ImageConverter.MAX_WEBP_SIZE,
                    max_height=ImageConverter.MAX_WEBP_SIZE,
                )
                if resized_data:
                    image = Image.open(BytesIO(resized_data))

            # Convert to RGB if necessary
            if image.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                if image.mode in ("RGBA", "LA"):
                    background.paste(image, mask=image.split()[-1])
                else:
                    background.paste(image)
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")

            # Convert to WebP
            output = BytesIO()
            image.save(output, format="WEBP", quality=quality, method=6)
            webp_data = output.getvalue()

            compression_ratio = len(webp_data) / len(image_data) * 100
            logger.debug(
                f"WebP conversion: {len(image_data)} → {len(webp_data)} bytes "
                f"({compression_ratio:.1f}%)"
            )

            return webp_data, len(webp_data)

        except Exception as e:
            logger.error(f"Error convert WebP: {e}")
            return None, 0

    @staticmethod
    def resize_image(
        image_data: bytes,
        max_width: int = None,
        max_height: int = None,
        maintain_aspect: bool = True,
    ) -> Tuple[Optional[bytes], int]:
        try:
            image = Image.open(BytesIO(image_data))
            original_size = image.size

            if max_width or max_height:
                if maintain_aspect:
                    image.thumbnail(
                        (max_width or 999999, max_height or 999999),
                        Image.Resampling.LANCZOS,
                    )
                else:
                    new_size = (max_width or image.width, max_height or image.height)
                    image = image.resize(new_size, Image.Resampling.LANCZOS)

            output = BytesIO()
            image.save(output, format=image.format or "PNG")
            resized_data = output.getvalue()

            logger.debug(f"Resized: {original_size} → {image.size}")

            return resized_data, len(resized_data)

        except Exception as e:
            logger.error(f"Lỗi resize ảnh: {e}")
            return None, 0
