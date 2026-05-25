#Yogiramsuratkumar Jaya Guru Raya!
import networkx as nx
import matplotlib.pyplot as plt
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

            #Map Endpoint Anchor
            self.graph.add_node(url, type="url", label=url)

            field_details = item.get("form_field_detail", [])
            meta_map = {f["name"]: f for f in field_details if "name" in f}

            for param in item.get("params", []):
                param_type = "standard_param"
                label =  param

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
        """Saves structural network patterns to a standardized JSON topology map."""
        payload = {
            "nodes": [{"id": n, "type": self.graph.nodes[n]["type"], "label": self.graph.nodes[n]["label"]} for n in self.graph.nodes],
            "links": [{"source": u, "target": v} for u, v in self.graph.edges]
        }
        DataStore.save_json(config.GRAPH_JSON_FILE, payload)

    def draw_graph(self):
        """Renders an interactive matplotlib visual layout based on entry points."""
        if not self.graph.nodes:
            print("[!] Graph is empty. Nothing to render.")
            return

        colors, sizes = [], []
        for node in self.graph:
            ntype = self.graph.nodes[node].get("type", "url")
            if ntype == "url":
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
        
        # Calculate optimal layout dispersion 
        pos = nx.spring_layout(self.graph, k=0.5, iterations=50)
        
        # 1. Draw the network nodes explicitly
        nx.draw_networkx_nodes(self.graph, pos, node_color=colors, node_size=sizes)
        
        # 2. Draw clean, prominent directional arrows using arrowstyle
        nx.draw_networkx_edges(
            self.graph, 
            pos, 
            arrowstyle="->", 
            arrowsize=18, 
            edge_color="#555555",  # Darker gray for high contrast visibility
            width=1.5,
            connectionstyle="arc3,rad=0.1"  # Subtle bend to prevent overlapping bi-directional paths
        )
        
        # 3. Add a small vertical offset to the text positions so labels hover neatly above nodes
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
        plt.axis("off")  # Removes background grid borders for a cleaner map feel
        plt.subplots_adjust(left=0.05, right=0.95, top=0.92, bottom=0.05)
        plt.show()