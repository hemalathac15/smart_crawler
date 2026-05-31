import json
import os
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime

class SecurityGraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph()

    def process_crawled_data(self, intel_feed):
        """
        Transforms dynamic crawler structured metrics into node configurations 
        and relational dependency interaction paths.
        """
        # Ensure we can handle both a single dictionary entry or a bulk list feed safely
        if isinstance(intel_feed, dict):
            intel_feed = [intel_feed]

        for item in intel_feed:
            source_url = item.get("url")
            if not source_url:
                continue

            # 1. Map Core Origin Node Context
            source_node_type = "api" if "/api/" in source_url.lower() else "page"
            self.graph.add_node(source_url, type=source_node_type, label=source_url)

            # 2. Map Dynamic Form Objects & Submission Target Endpoints
            for form in item.get("forms", []):
                target_action = form.get("action", source_url)
                form_method = form.get("method", "get").lower()
                
                # Register target action endpoint node
                action_node_type = "api" if form_method == "post" or "/api/" in target_action.lower() else "page"
                self.graph.add_node(target_action, type=action_node_type, label=target_action)
                
                # Draw edge representing the interactive transaction surface
                self.graph.add_edge(source_url, target_action, type="form_submit")

                # Trace Individual Input Fields linked to this submission context
                for form_input in form.get("inputs", []):
                    inp_name = form_input.get("name")
                    inp_type = form_input.get("type", "text")
                    
                    if inp_name:
                        param_node_id = f"{target_action}?param={inp_name}"
                        label = f"{inp_name}[{inp_type}]"
                        
                        # Set parameter priority classifications for graph visualization highlighting
                        self.graph.add_node(param_node_id, type=inp_type, label=label)
                        self.graph.add_edge(target_action, param_node_id, type="parameter_link")

            # 3. Map Live Background API Endpoints Discovered Over the Wire (via Client JS)
            for js_endpoint in item.get("endpoints_discovered_via_js", []):
                endpoint_url = js_endpoint.get("url")
                if endpoint_url:
                    self.graph.add_node(endpoint_url, type="api", label=endpoint_url)
                    self.graph.add_edge(source_url, endpoint_url, type="ajax_call")

            # 4. Map Discovered Standard Links (Navigation Redirects/References)
            for link in item.get("links", []):
                if link != source_url:
                    link_node_type = "api" if any(ext in link.lower() for ext in [".json", ".pdf", "/api/"]) else "page"
                    self.graph.add_node(link, type=link_node_type, label=link)
                    self.graph.add_edge(source_url, link, type="redirect")

    def export_graph_json(self):
        """Saves structured network patterns to a standardized JSON topology map matching the target schema."""
        nodes_payload = []
        url_to_id = {}

        # 1. Map nodes with sequential IDs (n1, n2, ...) to fit structural layout schemas
        for index, node in enumerate(self.graph.nodes, start=1):
            node_id = f"n{index}"
            url_to_id[node] = node_id
            
            internal_type = self.graph.nodes[node].get("type", "page")
            # Normalize complex parameter categories back to clean foundational schema classifications
            schema_type = "api" if internal_type in ["api", "hidden", "file"] else "page"

            nodes_payload.append({
                "id": node_id,
                "type": schema_type,
                "url": node  
            })

        # 2. Build edges payload mapping transitions via IDs
        edges_payload = []
        for u, v in self.graph.edges:
            edge_type = self.graph.edges[u, v].get("type", "redirect")

            edges_payload.append({
                "source": url_to_id[u],
                "target": url_to_id[v],
                "type": edge_type
            })

        # 3. Compile the schema payload
        payload = {
            "nodes": nodes_payload,
            "edges": edges_payload,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "total_nodes": len(nodes_payload),
                "total_edges": len(edges_payload)
            }
        }
        
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
                colors.append("#1f77b4")  # Cool blue for normal pages
                sizes.append(500)
            elif ntype == "api":
                colors.append("#2ca02c")  # Green for APIs/Webhooks
                sizes.append(400)
            elif ntype == "hidden":
                colors.append("#ff7f0e")  # Orange Warning flag for hidden properties
                sizes.append(300)
            elif ntype == "file":
                colors.append("#d62728")  # Red Attack Surface Risk for upload channels
                sizes.append(350)
            else:
                colors.append("#bcbd22")  # Olive hue for basic attributes/parameters
                sizes.append(150)

        plt.figure(figsize=(14, 9))
        
        # Spring layout with customized repulsion spacing (k) for text visibility
        pos = nx.spring_layout(self.graph, k=0.6, iterations=60)
        
        nx.draw_networkx_nodes(self.graph, pos, node_color=colors, node_size=sizes)
        
        # Extract edge type metadata dictionaries dynamically to apply styling variations if desired
        nx.draw_networkx_edges(
            self.graph, 
            pos, 
            arrowstyle="->", 
            arrowsize=15, 
            edge_color="#777777",
            width=1.2,
            connectionstyle="arc3,rad=0.08"
        )
        
        # Offset labels slightly above the nodes to maintain node color visibility
        label_pos = {node_id: [coords[0], coords[1] + 0.03] for node_id, coords in pos.items()}
        labels = nx.get_node_attributes(self.graph, 'label')
        
        # Clean up labels visually if they are excessively long URLs
        shortened_labels = {}
        for k, v in labels.items():
            if v.startswith("http"):
                parsed = v.replace("https://", "").replace("http://", "")
                shortened_labels[k] = parsed if len(parsed) < 35 else f"...{parsed[-32:]}"
            else:
                shortened_labels[k] = v

        nx.draw_networkx_labels(
            self.graph, 
            pos=label_pos, 
            labels=shortened_labels, 
            font_size=7, 
            font_weight="bold"
        )

        plt.title("Smart Crawler Application Attack Surface Topology Map", fontsize=13, weight="bold")
        plt.axis("off")
        plt.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.02)
        
        plt.savefig("output/fig_cyart.png", dpi=300, bbox_inches='tight')
        print("[*] Relationship canvas snapshot saved successfully to output/fig_cyart.png.")
        plt.show()