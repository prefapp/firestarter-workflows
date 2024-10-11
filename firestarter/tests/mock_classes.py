class DaggerContextMock():

    async def export(self, file_name: str) -> None:
        print(f"Called mock with file_name ${file_name}")

