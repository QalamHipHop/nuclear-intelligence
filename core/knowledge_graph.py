"""Nuclear Intelligence - Knowledge Graph - Advanced with Export"""
import os, json, hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from loguru import logger

class KnowledgeGraph:
    def __init__(self, path: str = "knowledge_base/knowledge_graph.json"):
        self.path = path
        self.graph = {"entities": {}, "relationships": [], "metadata": {"created": datetime.now().isoformat(), "version": "2.0", "last_updated": datetime.now().isoformat()}}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content.strip(): return
                    data = json.loads(content)
                    if isinstance(data, dict) and "entities" in data:
                        self.graph = data
                        logger.info(f"Loaded KG: {len(self.graph['entities'])} entities")
            except Exception as e:
                logger.error(f"KG load error: {e}")
                try: os.rename(self.path, self.path + f".bak{datetime.now().strftime('%Y%m%d')}")
                except: pass

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.graph["metadata"]["last_updated"] = datetime.now().isoformat()
        self.graph["metadata"]["entity_count"] = len(self.graph["entities"])
        temp_path = self.path + ".tmp"
        with open(temp_path, 'w', encoding='utf-8') as f: json.dump(self.graph, f, indent=4, ensure_ascii=False)
        if os.path.exists(temp_path): os.replace(temp_path, self.path)

    def add_knowledge(self, question: str, answer: str, metadata: Dict[str, Any]):
        entity_id = hashlib.sha256(question.encode()).hexdigest()[:16]
        self.graph["entities"][entity_id] = {
            "id": entity_id, "question": question, "answer_summary": answer[:500] + ("..." if len(answer)>500 else ""),
            "answer_full": answer, "metadata": metadata, "created_at": datetime.now().isoformat(), "access_count": 0, "verified": True
        }
        category = metadata.get("category", "General")
        self.graph["relationships"].append({"id": hashlib.sha256(f"{entity_id}_{category}".encode()).hexdigest()[:12], "from": entity_id, "to": category, "type": "belongs_to_category", "created_at": datetime.now().isoformat()})
        self._save()
        logger.info(f"Added entity: {question[:60]}...")

    def search_entities(self, query: str, limit: int = 10) -> List[Dict]:
        results = []
        q_lower = query.lower()
        for eid, entity in self.graph["entities"].items():
            if q_lower in entity.get("question","").lower() or q_lower in entity.get("answer_summary","").lower():
                entity["access_count"] = entity.get("access_count", 0) + 1
                results.append(entity)
                self.graph["entities"][eid]["access_count"] = entity["access_count"]
        results.sort(key=lambda x: x["access_count"], reverse=True)
        return results[:limit]

    def get_category_stats(self) -> Dict[str, int]:
        stats = {}
        for rel in self.graph["relationships"]:
            if rel["type"] == "belongs_to_category":
                stats[rel["to"]] = stats.get(rel["to"], 0) + 1
        return stats

    def get_recent_entities(self, limit: int = 10) -> List[Dict]:
        entities = sorted(self.graph["entities"].values(), key=lambda x: x.get("created_at",""), reverse=True)
        return entities[:limit]

    def get_top_entities(self, by: str = "accuracy", limit: int = 10) -> List[Dict]:
        entities = list(self.graph["entities"].values())
        if by == "accuracy": entities.sort(key=lambda x: x.get("metadata",{}).get("accuracy",0), reverse=True)
        elif by == "novelty": entities.sort(key=lambda x: x.get("metadata",{}).get("novelty",0), reverse=True)
        elif by == "access": entities.sort(key=lambda x: x.get("access_count",0), reverse=True)
        return entities[:limit]

    def export_json(self, path: Optional[str] = None) -> str:
        path = path or self.path.replace(".json", "_export.json")
        with open(path, 'w', encoding='utf-8') as f: json.dump(self.graph, f, indent=4, ensure_ascii=False)
        return path

    def export_markdown(self, path: Optional[str] = None) -> str:
        lines = [f"# Nuclear Intelligence Knowledge Graph\n**Generated:** {datetime.now().isoformat()}\n**Entities:** {len(self.graph['entities'])}\n"]
        stats = self.get_category_stats()
        lines.append("## Categories\n")
        for cat, count in sorted(stats.items(), key=lambda x: x[1], reverse=True): lines.append(f"- **{cat}**: {count}")
        lines.append("\n## Top Entities\n")
        for entity in self.get_top_entities("accuracy", 20):
            meta = entity.get("metadata", {})
            lines.append(f"### {entity['question'][:80]}...\n- Category: {meta.get('category')} | Accuracy: {meta.get('accuracy',0):.1f}% | Novelty: {meta.get('novelty',0):.1f}%\n")
        path = path or self.path.replace(".json", "_export.md")
        with open(path, 'w', encoding='utf-8') as f: f.write("\n".join(lines))
        return path

    def get_stats(self) -> Dict[str, Any]:
        return {"total_entities": len(self.graph["entities"]), "total_relationships": len(self.graph["relationships"]), "category_distribution": self.get_category_stats(), "latest_update": self.graph["metadata"].get("last_updated","N/A"), "version": self.graph["metadata"].get("version","unknown")}
