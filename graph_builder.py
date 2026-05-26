import json
import os
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime
from store import DataStore
import config

class SecurityGraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph()

    def process_crawled_data(self, intel_feed):
        """Transforms structural maps into node configurations and dependency branches."""
        for item in intel_feed:
            url = item.get("url")
            if not url:
                continue

            # Map Endpoint Anchor (Using the schema default type 'page' or 'api')
            node_type = "api" if any(indicator in url.lower() for indicator in ["/api/", "ajax", ".json"]) else "page"
            self.graph.add_node(url, type=node_type, label=url)

            field_details = item.get("form_field_detail", [])
            meta_map = {f["name"]: f for f in field_details if "name" in f}

            for param in item.get("params", []):
                param_type = "standard_param"
                label = param

                meta = meta_map.get(param)
                if meta:
                    if meta.get("hidden"):
                        param_type = "hidden"
                        label = f"{param}[hidden]"
                    elif meta.get("file"):
                        param_type = "file"
                        label = f"{param}[file]"
                        
                self.graph.add_node(param, type=param_type, label=label)
                self.graph.add_edge(url, param)

    def export_graph_json(self):
        """Saves structural network patterns to a standardized JSON topology map matching the target schema."""
        nodes_payload = []
        url_to_id = {}

        # 1. Map nodes with sequential IDs (n1, n2, ...) to fit the schema requirements
        for index, node in enumerate(self.graph.nodes, start=1):
            node_id = f"n{index}"
            url_to_id[node] = node_id
            
            # Normalize internal custom types back to core blueprint schema definitions ('page' or 'api')
            base_type = self.graph.nodes[node]["type"]
            schema_type = "api" if base_type in ["api", "hidden", "file"] else "page"

            nodes_payload.append({
                "id": node_id,
                "type": schema_type,
                "url": node  # The schema requires the 'url' key here
            })

        # 2. Build edges payload using node IDs and infer transit classification
        edges_payload = []
        for u, v in self.graph.edges:
            target_type = self.graph.nodes[v]["type"]
            
            # Match schema interaction edge types ('form_submit', 'ajax_call', 'redirect')
            edge_type = "redirect"
            if target_type == "file" or "api" in v.lower():
                edge_type = "ajax_call"
            elif target_type == "hidden":
                edge_type = "form_submit"

            edges_payload.append({
                "source": url_to_id[u],
                "target": url_to_id[v],
                "type": edge_type
            })

        # 3. Form the structural payload matching the blueprint schema exactly
        payload = {
            "nodes": nodes_payload,
            "edges": edges_payload,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "total_nodes": len(nodes_payload),
                "total_edges": len(edges_payload)
            }
        }
        
        # Save JSON data using your DataStore router
        os.makedirs("output", exist_ok=True)
        with open("output/graph_output.json", "w") as f:
            json.dump(payload, f, indent=4)
        print("[*] Successfully generated output/graph_output.json.")

    def draw_graph(self):
        """Renders an interactive matplotlib visual layout and exports a PNG asset copy."""
        if not self.graph.nodes:
            print("[!] Graph is empty. Nothing to render.")
            return

        colors, sizes = [], []
        for node in self.graph:
            ntype = self.graph.nodes[node].get("type", "page")
            if ntype in ["page", "url"]:
                colors.append("#1f77b4")
                sizes.append(600)
            elif ntype == "hidden":
                colors.append("#ff7f0e")  # Orange Warning
                sizes.append(400)
            elif ntype == "file":
                colors.append("#d62728")  # Red Attack Risk
                sizes.append(450)
            else:
                colors.append("#2ca02c")  # Standard Parameter
                sizes.append(200)

        plt.figure(figsize=(12, 8))
        
        pos = nx.spring_layout(self.graph, k=0.5, iterations=50)
        
        nx.draw_networkx_nodes(self.graph, pos, node_color=colors, node_size=sizes)
        
        nx.draw_networkx_edges(
            self.graph, 
            pos, 
            arrowstyle="->", 
            arrowsize=18, 
            edge_color="#555555",
            width=1.5,
            connectionstyle="arc3,rad=0.1"
        )
        
        label_pos = {node_id: [coords[0], coords[1] + 0.04] for node_id, coords in pos.items()}
        labels = nx.get_node_attributes(self.graph, 'label')
        
        nx.draw_networkx_labels(
            self.graph, 
            label_pos, 
            labels=labels, 
            font_size=8, 
            font_weight="bold"
        )

        plt.title("smart_crawler Attack Surface Map Layout", fontsize=14, weight="bold")
        plt.axis("off")
        plt.subplots_adjust(left=0.05, right=0.95, top=0.92, bottom=0.05)
        
        # Automatically saves a static file image copy inside the output folder
        plt.savefig("output/fig_cyart.png", dpi=300, bbox_inches='tight')
        print("[*] Relationship canvas snapshot saved successfully to output/fig_cyart.png.")
        
        plt.show()