from neo4j import AsyncGraphDatabase
from app.config import settings


class Neo4jSession:
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    async def close(self):
        await self.driver.close()

    async def run(self, query: str, parameters: dict = None) -> list:
        """Run a cypher query and return the records as a list of dicts."""
        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records


neo4j_client = Neo4jSession()


async def get_neo4j():
    """Dependency for getting neo4j client."""
    yield neo4j_client
