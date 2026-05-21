import json
import os
from collections import Counter
import networkx as nx

class GraphifyHeuristicParser:
    def __init__(self, manifest_path):
        self.manifest_path = manifest_path
        self.nodes = []
        self.edges = []
        self.graph = nx.DiGraph()
        
    def load_manifest(self):
        """Graphify output directory se json fetch karke metadata state build karta hai."""
        if not os.path.exists(self.manifest_path):
            raise FileNotFoundError(f"Graphify manifest not found at: {self.manifest_path}")
            
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Graphify standard keys matching
            self.nodes = data.get("nodes", [])
            self.edges = data.get("edges", [])
            
        # NetworkX Direct Graph initialize karna dependency metrics ke liye
        for node in self.nodes:
            self.graph.add_node(node.get("id"), type=node.get("type", "unknown"))
        for edge in self.edges:
            self.graph.add_edge(edge.get("source"), edge.get("target"), relation=edge.get("type"))

    def detect_architecture_pattern(self):
        """Graph parameters aur patterns ke baseline distribution se architecture matrix design karta hai."""
        node_ids = [str(node.get("id")).lower() for node in self.nodes]
        
        # Suffix matching heuristics
        controller_count = sum(1 for nid in node_ids if "controller" in nid)
        service_count = sum(1 for nid in node_ids if "service" in nid)
        repo_count = sum(1 for nid in node_ids if "repository" in nid or "repo" in nid)
        helper_count = sum(1 for nid in node_ids if "helper" in nid or "util" in nid)
        
        if controller_count > 0 and service_count > 0:
            return f"Layered Architecture (MVC / Clean Architecture Pattern) - Detected {controller_count} Controllers, {service_count} Services."
        elif service_count > 5 and repo_count == 0:
            return "Domain-Driven Flat Architecture (Services Heavy without decoupled Repository persistence)."
        elif helper_count > len(self.nodes) * 0.3:
            return "Utility/Helper Heavy Monolithic structure - High structural coupling detected."
        else:
            return "Flat/Standard Monolithic Layout or Custom Object-Oriented Pattern."

    def extract_naming_conventions(self):
        """Methods aur classes ke naming heuristics calculate karta hai."""
        method_names = []
        class_names = []
        async_count = 0
        
        for node in self.nodes:
            node_id = str(node.get("id", ""))
            node_type = node.get("type", "").lower()
            
            if node_type == "class":
                class_names.append(node_id)
            elif node_type == "method":
                method_names.append(node_id)
                if node_id.endswith("Async"):
                    async_count += 1
                    
        # Basic character checking logic
        is_pascal_case = any(name[0].isupper() for name in class_names if name) if class_names else True
        
        heuristics = {
            "class_naming": "PascalCase (Preferred)" if is_pascal_case else "camelCase/Mixed",
            "async_pattern": "Strict Async Suffix Enforced" if async_count > len(method_names) * 0.4 else "Inconsistent Async Naming Patterns",
            "total_methods_scanned": len(method_names)
        }
        return heuristics

    def identify_structural_hotspots(self):
        """NetworkX implementation using structural degree weight matrix to detect God Classes."""
        if len(self.nodes) == 0:
            return []
            
        # In-degree: Kaun si files sabse zyada inject ya reference ho rahi hain (Core Models/Utilities)
        # Out-degree: Kaun si files sabse zyada external systems call kar rahi hain (Orchestrators/God Classes)
        out_degrees = dict(self.graph.out_degree())
        
        # Sort files by highest outbound dependencies
        sorted_hotspots = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)
        
        # Filter classes that control too many components (Threshold > 4 connections)
        god_nodes = [node for node, score in sorted_hotspots if score > 4][:3]
        return god_nodes

    def compile_heuristics_payload(self):
        """Saare heuristics pipeline matrices ko single context packet mein bundle karta hai."""
        self.load_manifest()
        
        architecture = self.detect_architecture_pattern()
        naming = self.extract_naming_conventions()
        god_classes = self.identify_structural_hotspots()
        
        payload = {
            "metrics": {
                "total_files_analyzed": len(self.nodes),
                "total_dependency_edges": len(self.edges)
            },
            "architecture_type": architecture,
            "naming_pattern": f"Classes: {naming['class_naming']} | Methods: {naming['async_pattern']}",
            "god_classes": god_classes if god_classes else "None (Codebase architecture is highly decoupled and modular)"
        }
        return payload

# Local CLI Testing Gateway
if __name__ == "__main__":
    # Assuming execution from project directory pointing to a test graphify output
    test_path = "./graphify-out/manifest.json"
    if os.path.exists(test_path):
        parser = GraphifyHeuristicParser(test_path)
        analysis_result = parser.compile_heuristics_payload()
        print(json.dumps(analysis_result, indent=2))