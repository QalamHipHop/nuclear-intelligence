"""
Nuclear Intelligence v3.0 - Enhanced Knowledge Graph
═══════════════════════════════════════════════════════════════════
Advanced graph with:
- Entity relationships
- Category management
- Advanced search
- Export capabilities
- Statistics and analytics
- Version control
═══════════════════════════════════════════════════════════════════
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple
from loguru import logger
from collections import defaultdict


class KnowledgeGraph:
    """Enhanced knowledge graph with advanced features"""

    def __init__(self, path: str = "knowledge_base/knowledge_graph.json"):
        self.path = path

        # Graph structure
        self.graph: Dict[str, Any] = {
            "entities": {},           # entity_id -> entity data
            "relationships": [],       # relationship links
            "categories": {},         # category metadata
            "metadata": {
                "created": datetime.now().isoformat(),
                "version": "3.0",
                "last_updated": datetime.now().isoformat(),
                "total_entities": 0,
                "total_relationships": 0,
            }
        }

        # Index for fast lookups
        self._entity_index: Dict[str, Set[str]] = defaultdict(set)  # word -> entity_ids
        self._category_index: Dict[str, Set[str]] = defaultdict(set)  # category -> entity_ids
        self._tag_index: Dict[str, Set[str]] = defaultdict(set)  # tag -> entity_ids

        self._load()

    def _load(self):
        """Load graph from disk"""
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        if isinstance(data, dict) and "entities" in data:
                            self.graph = data
                            self._rebuild_indices()
                            logger.info(f"📚 Loaded KG: {len(self.graph['entities'])} entities")
                        else:
                            logger.warning("Invalid KG format, starting fresh")
            except json.JSONDecodeError as e:
                logger.error(f"KG JSON error: {e}")
                self._backup_and_reset()
            except Exception as e:
                logger.error(f"KG load error: {e}")
                self._backup_and_reset()
        else:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            self._save()

    def _backup_and_reset(self):
        """Backup corrupted file and reset"""
        try:
            backup_path = self.path + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            if os.path.exists(self.path):
                os.rename(self.path, backup_path)
                logger.info(f"📦 Backed up corrupted KG to: {backup_path}")
        except:
            pass
        self.graph = self._get_empty_graph()
        self._save()

    def _get_empty_graph(self) -> Dict:
        return {
            "entities": {},
            "relationships": [],
            "categories": {},
            "metadata": {
                "created": datetime.now().isoformat(),
                "version": "3.0",
                "last_updated": datetime.now().isoformat(),
            }
        }

    def _save(self):
        """Save graph to disk atomically"""
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            self.graph["metadata"]["last_updated"] = datetime.now().isoformat()
            self.graph["metadata"]["total_entities"] = len(self.graph["entities"])
            self.graph["metadata"]["total_relationships"] = len(self.graph["relationships"])

            temp_path = self.path + ".tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self.graph, f, indent=4, ensure_ascii=False)
            os.replace(temp_path, self.path)
        except Exception as e:
            logger.error(f"💾 Save error: {e}")

    def _rebuild_indices(self):
        """Rebuild search indices"""
        self._entity_index.clear()
        self._category_index.clear()
        self._tag_index.clear()

        for eid, entity in self.graph.get("entities", {}).items():
            # Index by words in question
            question = entity.get("question", "").lower()
            words = set(question.split())
            for word in words:
                if len(word) > 2:
                    self._entity_index[word].add(eid)

            # Index by category
            meta = entity.get("metadata", {})
            category = meta.get("category", "General")
            self._category_index[category].add(eid)

            # Index by keywords
            keywords = meta.get("keywords", [])
            for kw in keywords:
                self._tag_index[kw.lower()].add(eid)

    def _index_entity(self, entity_id: str, question: str, category: str, keywords: List[str]):
        """Index a new entity"""
        # Word index
        words = set(question.lower().split())
        for word in words:
            if len(word) > 2:
                self._entity_index[word].add(entity_id)

        # Category index
        self._category_index[category].add(entity_id)

        # Tag index
        for kw in keywords:
            self._tag_index[kw.lower()].add(entity_id)

    def add_knowledge(
        self,
        question: str,
        answer: str,
        metadata: Dict[str, Any],
        entity_id: Optional[str] = None,
    ):
        """Add new knowledge to the graph"""
        # Generate entity ID
        if not entity_id:
            entity_id = hashlib.sha256(question.encode()).hexdigest()[:16]

        # Create entity
        entity = {
            "id": entity_id,
            "question": question,
            "answer_summary": answer[:500] + ("..." if len(answer) > 500 else ""),
            "answer_full": answer,
            "metadata": metadata,
            "created_at": datetime.now().isoformat(),
            "access_count": 0,
            "verified": metadata.get("accuracy", 0) >= 80,
            "version": "3.0",
            "relationships": [],
        }

        # Add to graph
        self.graph["entities"][entity_id] = entity

        # Create category relationship
        category = metadata.get("category", "General")
        rel_id = hashlib.sha256(f"{entity_id}_{category}".encode()).hexdigest()[:12]
        self.graph["relationships"].append({
            "id": rel_id,
            "from": entity_id,
            "to": category,
            "type": "belongs_to_category",
            "created_at": datetime.now().isoformat(),
        })

        # Create difficulty relationship
        difficulty = metadata.get("difficulty", 5)
        rel_id2 = hashlib.sha256(f"{entity_id}_difficulty".encode()).hexdigest()[:12]
        self.graph["relationships"].append({
            "id": rel_id2,
            "from": entity_id,
            "to": f"difficulty_{difficulty}",
            "type": "has_difficulty",
            "created_at": datetime.now().isoformat(),
        })

        # Update category metadata
        if category not in self.graph["categories"]:
            self.graph["categories"][category] = {
                "name": category,
                "count": 0,
                "avg_accuracy": 0,
                "created": datetime.now().isoformat(),
            }
        cat_data = self.graph["categories"][category]
        cat_data["count"] += 1
        cat_data["avg_accuracy"] = (
            (cat_data["avg_accuracy"] * (cat_data["count"] - 1) + metadata.get("accuracy", 0))
            / cat_data["count"]
        )

        # Index entity
        keywords = metadata.get("keywords", [])
        self._index_entity(entity_id, question, category, keywords)

        # Save
        self._save()
        logger.info(f"✅ Added entity: {question[:60]}... [{category}]")

    def update_entity(self, entity_id: str, updates: Dict) -> bool:
        """Update an existing entity"""
        if entity_id not in self.graph["entities"]:
            return False

        entity = self.graph["entities"][entity_id]
        entity.update(updates)
        entity["updated_at"] = datetime.now().isoformat()

        self._save()
        return True

    def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity"""
        if entity_id not in self.graph["entities"]:
            return False

        # Remove entity
        del self.graph["entities"][entity_id]

        # Remove relationships
        self.graph["relationships"] = [
            r for r in self.graph["relationships"]
            if r.get("from") != entity_id
        ]

        # Rebuild indices
        self._rebuild_indices()

        self._save()
        return True

    def search_entities(
        self,
        query: str,
        limit: int = 10,
        category: Optional[str] = None,
        min_accuracy: float = 0,
    ) -> List[Dict]:
        """Advanced entity search"""
        results = []
        q_lower = query.lower()
        q_words = q_lower.split()

        # Score each entity
        entity_scores = {}
        for eid, entity in self.graph["entities"].items():
            score = 0
            question = entity.get("question", "").lower()
            answer = entity.get("answer_summary", "").lower()
            meta = entity.get("metadata", {})

            # Exact match bonus
            if q_lower in question:
                score += 100

            # Word match
            for word in q_words:
                if word in question:
                    score += 20
                if word in answer:
                    score += 10
                if word in str(meta.get("keywords", [])):
                    score += 30

            # Category filter
            if category and meta.get("category") != category:
                continue

            # Accuracy filter
            if meta.get("accuracy", 0) < min_accuracy:
                continue

            if score > 0:
                entity_scores[eid] = score

        # Sort by score
        sorted_ids = sorted(entity_scores.keys(), key=lambda x: entity_scores[x], reverse=True)

        # Get top results
        for eid in sorted_ids[:limit]:
            entity = self.graph["entities"][eid].copy()
            entity["_score"] = entity_scores[eid]
            entity["access_count"] = entity.get("access_count", 0) + 1
            results.append(entity)

        return results

    def get_category_stats(self) -> Dict[str, int]:
        """Get category distribution"""
        stats = {}
        for rel in self.graph.get("relationships", []):
            if rel.get("type") == "belongs_to_category":
                cat = rel.get("to", "Unknown")
                stats[cat] = stats.get(cat, 0) + 1
        return stats

    def get_recent_entities(self, limit: int = 10) -> List[Dict]:
        """Get most recently created entities"""
        entities = sorted(
            self.graph["entities"].values(),
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        return entities[:limit]

    def get_top_entities(
        self,
        by: str = "accuracy",
        limit: int = 10,
        category: Optional[str] = None,
    ) -> List[Dict]:
        """Get top entities by metric"""
        entities = list(self.graph["entities"].values())

        # Filter by category
        if category:
            entities = [e for e in entities if e.get("metadata", {}).get("category") == category]

        # Sort
        if by == "accuracy":
            entities.sort(key=lambda x: x.get("metadata", {}).get("accuracy", 0), reverse=True)
        elif by == "novelty":
            entities.sort(key=lambda x: x.get("metadata", {}).get("novelty", 0), reverse=True)
        elif by == "access":
            entities.sort(key=lambda x: x.get("access_count", 0), reverse=True)
        elif by == "completeness":
            entities.sort(key=lambda x: x.get("metadata", {}).get("completeness", 0), reverse=True)

        return entities[:limit]

    def get_entities_by_category(self, category: str, limit: int = 50) -> List[Dict]:
        """Get all entities in a category"""
        return self.get_top_entities(by="accuracy", limit=limit, category=category)

    def get_difficulty_distribution(self) -> Dict[int, int]:
        """Get distribution of entities by difficulty"""
        dist = defaultdict(int)
        for entity in self.graph["entities"].values():
            diff = entity.get("metadata", {}).get("difficulty", 5)
            dist[diff] += 1
        return dict(sorted(dist.items()))

    def get_time_series(self, interval: str = "day", limit: int = 30) -> List[Dict]:
        """Get entity creation time series"""
        from collections import Counter

        timestamps = []
        for entity in self.graph["entities"].values():
            ts = entity.get("created_at", "")[:10]  # YYYY-MM-DD
            if ts:
                timestamps.append(ts)

        counter = Counter(timestamps)
        return [{"date": k, "count": v} for k, v in sorted(counter.items(), reverse=True)[:limit]]

    def get_correlations(self) -> Dict:
        """Find entity correlations based on categories and keywords"""
        correlations = defaultdict(int)

        for entity in self.graph["entities"].values():
            meta = entity.get("metadata", {})
            keywords = meta.get("keywords", [])

            # Count keyword pairs
            for i, kw1 in enumerate(keywords):
                for kw2 in keywords[i+1:]:
                    pair = tuple(sorted([kw1.lower(), kw2.lower()]))
                    correlations[pair] += 1

        # Return top correlations
        top = sorted(correlations.items(), key=lambda x: x[1], reverse=True)[:20]
        return {f"{k[0]}-{k[1]}": v for k, v in top}

    def export_json(self, path: Optional[str] = None) -> str:
        """Export graph as JSON"""
        path = path or self.path.replace(".json", "_export.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.graph, f, indent=4, ensure_ascii=False)
        return path

    def export_markdown(self, path: Optional[str] = None) -> str:
        """Export graph as Markdown"""
        lines = [
            f"# Nuclear Intelligence Knowledge Graph v3.0",
            f"**Generated:** {datetime.now().isoformat()}",
            f"**Total Entities:** {len(self.graph['entities'])}",
            f"**Total Relationships:** {len(self.graph['relationships'])}",
            "",
        ]

        # Categories section
        stats = self.get_category_stats()
        lines.append("## Categories\n")
        for cat, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{cat}**: {count} entities")

        # Top entities
        lines.append("\n## Top Entities (by Accuracy)\n")
        for entity in self.get_top_entities("accuracy", 20):
            meta = entity.get("metadata", {})
            lines.append(
                f"### {entity['question'][:100]}...\n"
                f"- Category: {meta.get('category')}\n"
                f"- Accuracy: {meta.get('accuracy', 0):.1f}%\n"
                f"- Novelty: {meta.get('novelty', 0):.1f}%\n"
                f"- Difficulty: {meta.get('difficulty', 'N/A')}/10\n"
                f"- Created: {entity.get('created_at', '')[:10]}\n"
            )

        path = path or self.path.replace(".json", "_export.md")
        with open(path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        return path

    def export_csv(self, path: Optional[str] = None) -> str:
        """Export entities as CSV"""
        import csv

        path = path or self.path.replace(".json", "_export.csv")
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "Question", "Category", "Difficulty",
                "Accuracy", "Novelty", "Usefulness", "Created"
            ])

            for entity in self.graph["entities"].values():
                meta = entity.get("metadata", {})
                writer.writerow([
                    entity.get("id", ""),
                    entity.get("question", "")[:200],
                    meta.get("category", ""),
                    meta.get("difficulty", ""),
                    meta.get("accuracy", ""),
                    meta.get("novelty", ""),
                    meta.get("usefulness", ""),
                    entity.get("created_at", "")[:10],
                ])
        return path

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics"""
        entities = self.graph.get("entities", {})

        # Calculate averages
        accuracies = [e.get("metadata", {}).get("accuracy", 0) for e in entities.values()]
        novelties = [e.get("metadata", {}).get("novelty", 0) for e in entities.values()]

        return {
            "total_entities": len(entities),
            "total_relationships": len(self.graph.get("relationships", [])),
            "category_distribution": self.get_category_stats(),
            "difficulty_distribution": self.get_difficulty_distribution(),
            "avg_accuracy": sum(accuracies) / max(len(accuracies), 1),
            "avg_novelty": sum(novelties) / max(len(novelties), 1),
            "verified_entities": sum(1 for e in entities.values() if e.get("verified")),
            "latest_update": self.graph["metadata"].get("last_updated", "N/A"),
            "version": self.graph["metadata"].get("version", "unknown"),
        }


__all__ = ['KnowledgeGraph']