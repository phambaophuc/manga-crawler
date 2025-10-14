import logging
from dotenv import load_dotenv
from prisma import Prisma


load_dotenv()


class DatabaseManager:
    def __init__(self):
        self.db = Prisma()
        self.logger = logging.getLogger(__name__)

    async def connect(self):
        try:
            await self.db.connect()
            self.logger.info("✅ Đã kết nối database")
            return True
        except Exception as e:
            self.logger.error(f"❌ Lỗi kết nối database: {e}")
            return False

    async def disconnect(self):
        try:
            await self.db.disconnect()
            self.logger.info("✅ Đã ngắt kết nối database")
        except Exception as e:
            self.logger.error(f"❌ Lỗi khi ngắt kết nối: {e}")

    async def health_check(self):
        try:
            count = await self.db.mangasource.count()
            self.logger.info(f"✅ Database health check passed. Sources count: {count}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Database health check failed: {e}")
            return False
