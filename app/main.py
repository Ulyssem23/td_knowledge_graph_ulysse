import os
from fastapi import FastAPI
from pydantic import BaseModel
from neo4j import GraphDatabase

app = FastAPI()

NEO4J_URI = os.getenv("NEO4J_URI","neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER","neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD","password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

@app.get('/health')
def health():
    # check neo4j connectivity
    try:
        with driver.session() as s:
            res = s.run("RETURN 1 AS ok").single()
            ok = res["ok"] == 1
    except Exception:
        ok = False
    return {"ok": ok}

class RecRequest(BaseModel):
    product_id: str
    k: int = 5

@app.post('/recs')
def recs(req: RecRequest):
    """
    Simple co-occurrence based recommendations:
    Finds products frequently bought together with the provided product_id using paths via orders.
    """
    q = '''
    MATCH (p:Product {id:$pid})<-[:CONTAINS]-(:Order)-[:CONTAINS]->(rec:Product)
    RETURN rec.id AS id, rec.name AS name, count(*) AS score
    ORDER BY score DESC LIMIT $k
    '''
    with driver.session() as s:
        rows = s.run(q, pid=req.product_id, k=req.k)
        return {"product": req.product_id, "recs": [dict(r) for r in rows]}
