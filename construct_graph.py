#!/usr/bin/env python3
import os
import sys
import json
import argparse
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from networkx.algorithms.link_analysis.pagerank_alg import _pagerank_python

# maintain same colors as your interactive graph
TYPE_COLORS = {
    "GOVERNMENT": "#4285F4",
    "SCHOLARLY":  "#0F9D58",
    "OTHER":      "#DB4437"
}

def is_valid_url(url):
    """Check if a string is a valid URL"""
    return url.startswith("http://") or url.startswith("https://")

def process_folder(directory="IDs"):
    """
    Reads all .json files in the directory and builds a graph.
    Each file becomes a GOVERNMENT node (id = filename minus .json).
    Each JSON object (one per line) in a file becomes an edge from that GOVERNMENT node
    to another node. For SCHOLARLY and GOVERNMENT types, the node id is taken from the object's "id" field;
    for OTHER types, the URL from the "id" field is used.
    """
    if not os.path.isdir(directory):
        sys.exit("Error: Directory '{}' does not exist.".format(directory))
    
    graph = {"nodes": {}, "edges": []}

    for filename in os.listdir(directory):
        if not filename.endswith(".json"):
            continue
        
        # Government node (source)
        gov_node_id = filename[:-5]  # Remove ".json"
        if gov_node_id not in graph["nodes"]:
            graph["nodes"][gov_node_id] = {
                "type": "GOVERNMENT",
                "title": gov_node_id,
                "label": gov_node_id
            }
        
        file_path = os.path.join(directory, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    print("Error parsing line in {}: {}".format(filename, line))
                    continue

                citation_type = obj.get("type", "").upper()
                if citation_type not in ["GOVERNMENT", "SCHOLARLY", "OTHER"]:
                    continue  # Skip UNKNOWN types
                
                # Get target node ID
                if citation_type == "OTHER":
                    citation_id = obj.get("id")
                    if not citation_id or not is_valid_url(citation_id):
                        continue  # Skip if no valid URL
                else:
                    citation_id = obj.get("id")
                    if not citation_id:
                        continue

                # Add target node if it doesn't exist
                if citation_id not in graph["nodes"]:
                    graph["nodes"][citation_id] = {
                        "type": citation_type,
                        "title": obj.get("title", citation_id),
                        "label": obj.get("title", citation_id),
                        "citation": obj.get("citation", ""),
                        "authors": obj.get("authors", []),
                        "date": obj.get("date", ""),
                        "links": obj.get("links", [])
                    }
                
                # Add edge
                graph["edges"].append({"from": gov_node_id, "to": citation_id})
    
    return graph

def revise_graph_model(graph_model):
    """
    Removes duplicate edges and any edge referencing a missing node.
    """
    # Remove duplicate edges
    unique_edges = []
    seen = set()
    for edge in graph_model.get("edges", []):
        edge_tuple = (edge.get("from"), edge.get("to"))
        if edge_tuple not in seen:
            seen.add(edge_tuple)
            unique_edges.append(edge)
    graph_model["edges"] = unique_edges

    # Remove edges with missing nodes
    valid_edges = []
    for edge in graph_model["edges"]:
        if edge.get("from") in graph_model["nodes"] and edge.get("to") in graph_model["nodes"]:
            valid_edges.append(edge)
    graph_model["edges"] = valid_edges

    return graph_model

def draw_interactive_graph(graph_data, output_html="citation_network.html"):
    """
    Creates an interactive visualization using Pyvis
    """
    try:
        from pyvis.network import Network
    except ImportError:
        sys.exit("Pyvis is required for interactive visualization. Please install it via pip (pip install pyvis).")
    
    net = Network(
        height="750px",
        width="100%",
        directed=True,
        notebook=False,
        cdn_resources='remote',
        bgcolor="#ffffff",
        font_color="black"
    )
    
    # Configure physics for better layout
    net.force_atlas_2based(
        gravity=-50,
        central_gravity=0.01,
        spring_length=100,
        spring_strength=0.08,
        damping=0.4,
        overlap=0
    )
    
    # Add nodes with properties
    for node_id, attributes in graph_data["nodes"].items():
        node_type = attributes.get("type", "").upper()
        
        # Set node color based on type
        if node_type == "GOVERNMENT":
            color = "#4285F4"  # Google blue
            size = 25
            shape = "diamond"
        elif node_type == "SCHOLARLY":
            color = "#0F9D58"  # Google green
            size = 20
            shape = "dot"
        elif node_type == "OTHER":
            color = "#DB4437"  # Google red
            size = 15
            shape = "dot"
        else:
            continue  # Shouldn't happen as we filtered earlier
        
        # Create tooltip content
        title = "<b>{}</b>".format(attributes.get("title", node_id))
        if attributes.get("citation"):
            title += "<br><br>{}".format(attributes["citation"])
        if attributes.get("date"):
            title += "<br><br>Date: {}".format(attributes["date"])
        
        net.add_node(
            node_id,
            label=attributes.get("label", node_id),
            title=title,
            color=color,
            size=size,
            shape=shape,
            borderWidth=1
        )
    
    # Add edges
    for edge in graph_data["edges"]:
        net.add_edge(
            edge["from"],
            edge["to"],
            arrows="to",
            physics=True
        )
    
    # Customize options
    net.set_options("""
    {
        "nodes": {
            "font": {
                "size": 12,
                "face": "arial"
            },
            "shadow": {
                "enabled": true,
                "color": "rgba(0,0,0,0.5)",
                "size": 10,
                "x": 5,
                "y": 5
            }
        },
        "edges": {
            "smooth": {
                "type": "continuous"
            },
            "shadow": {
                "enabled": true
            }
        },
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -50,
                "centralGravity": 0.01,
                "springLength": 100,
                "springConstant": 0.08,
                "damping": 0.4,
                "avoidOverlap": 0
            },
            "minVelocity": 0.75,
            "solver": "forceAtlas2Based"
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 200,
            "hideEdgesOnDrag": true,
            "multiselect": true
        }
    }
    """)
    
    # Add legend
    legend_html = """
    <div style="position: absolute; top: 10px; left: 10px; z-index: 1000; background: white; padding: 10px; border: 1px solid #ccc; border-radius: 5px;">
        <h3 style="margin-top: 0;">Node Types</h3>
        <div><span style="display: inline-block; width: 15px; height: 15px; background: #4285F4; border-radius: 50%; margin-right: 5px;"></span> Government</div>
        <div><span style="display: inline-block; width: 15px; height: 15px; background: #0F9D58; border-radius: 50%; margin-right: 5px;"></span> Scholarly</div>
        <div><span style="display: inline-block; width: 15px; height: 15px; background: #DB4437; border-radius: 50%; margin-right: 5px;"></span> Other</div>
    </div>
    """
    
    # Save to HTML file
    net.save_graph(output_html)
    
    # Add legend to the HTML file
    with open(output_html, 'r') as f:
        html_content = f.read()
    
    # Insert the legend just before the closing </body> tag
    html_content = html_content.replace('</body>', legend_html + '</body>')
    
    with open(output_html, 'w') as f:
        f.write(html_content)
    
    print("Interactive graph saved to {}".format(output_html))

def analyze_graph(graph_data):
    """Print basic graph statistics"""
    G = nx.DiGraph()
    for node_id, attributes in graph_data["nodes"].items():
        G.add_node(node_id, **attributes)
    for edge in graph_data["edges"]:
        G.add_edge(edge["from"], edge["to"])

    print("\nGraph Analysis:")
    print("Number of nodes: {}".format(G.number_of_nodes()))
    print("Number of edges: {}".format(G.number_of_edges()))

    # Count node types
    type_counts = defaultdict(int)
    for _, data in G.nodes(data=True):
        typ = data.get("type", "").upper()
        type_counts[typ] += 1

    print("\nNode types:")
    for typ, count in type_counts.items():
        print(f"{typ}: {count}")

    # Top cited/out nodes
    in_degrees = dict(G.in_degree())
    out_degrees = dict(G.out_degree())
    top_cited = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:5]
    top_citers = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)[:5]

    print("\nTop cited nodes:")
    for node, count in top_cited:
        print(f"{node}: {count} citations")
    print("\nMost citing nodes:")
    for node, count in top_citers:
        print(f"{node}: {count} references")


"""
def plot_centrality_histograms(graph_data, output_dir="centrality_plots", bins=20):
    
    Compute degree centrality, betweenness centrality, and PageRank,
    then plot three histogram‐style bar charts (side by side) with the
    y-axis max set to (highest bin count + 50).
    
    # Build graph
    G = nx.DiGraph()
    for nid, attrs in graph_data["nodes"].items():
        G.add_node(nid, **attrs)
    for e in graph_data["edges"]:
        G.add_edge(e["from"], e["to"])

    # Compute centralities
    deg_cent = nx.degree_centrality(G)
    btw_cent = nx.betweenness_centrality(G)
    try:
        pr = nx.pagerank(G)
    except Exception:
        pr = {}

    # Prepare grouping
    types = ["GOVERNMENT", "SCHOLARLY", "OTHER"]
    measures = {
        "degree": deg_cent,
        "betweenness": btw_cent,
        "pagerank": pr
    }

    os.makedirs(output_dir, exist_ok=True)

    for name, cent_dict in measures.items():
        # Collect values per type
        vals = {t: [] for t in types}
        for nid, data in G.nodes(data=True):
            t = data.get("type","").upper()
            if t in vals:
                vals[t].append(cent_dict.get(nid, 0.0))

        # Find common bin edges
        all_vals = np.concatenate(list(vals.values()))
        bin_edges = np.histogram_bin_edges(all_vals, bins=bins)

        # Compute histograms
        counts = {t: np.histogram(vals[t], bins=bin_edges)[0] for t in types}

        # Bar positioning
        width = (bin_edges[1] - bin_edges[0]) / (len(types) + 1)
        x = bin_edges[:-1]
        plt.figure()
        for i, t in enumerate(types):
            plt.bar(x + i*width, counts[t], width=width, label=t)

        # y-axis scaling
        max_count = max(c.max() for c in counts.values())
        plt.ylim(0, max_count + 50)

        plt.title(f"{name.capitalize()} Centrality Distribution by Document Type")
        plt.xlabel(f"{name.capitalize()} Centrality")
        plt.ylabel("Number of Nodes")
        plt.legend()
        plt.tight_layout()
        fn = os.path.join(output_dir, f"{name}_centrality_histogram.png")
        plt.savefig(fn)
        plt.close()
        print(f"  → {fn}")
"""

TYPE_COLORS = {
    "GOVERNMENT": "#4285F4",
    "SCHOLARLY":  "#0F9D58",
    "OTHER":      "#DB4437"
}

def plot_centrality_histograms(graph_data, output_dir="centrality_plots", bins=20):
    """
    For each centrality measure (degree, betweenness, pagerank), 
    compute using NetworkX (with SciPy fallback for pagerank), bin via NumPy,
    then print & plot per doc type.
    """
    # Build directed graph
    G = nx.DiGraph()
    for nid, attrs in graph_data["nodes"].items():
        G.add_node(nid, **attrs)
    for e in graph_data["edges"]:
        G.add_edge(e["from"], e["to"])

    # Prepare centrality functions
    cent_funcs = {
        "degree":      nx.degree_centrality,
        "betweenness": nx.betweenness_centrality,
        "pagerank":    None,  # we’ll handle this one specially
    }

    os.makedirs(output_dir, exist_ok=True)
    types = ["GOVERNMENT", "SCHOLARLY", "OTHER"]

    for name, func in cent_funcs.items():
        # compute centrality dict
        if name == "pagerank":
            try:
                cent_dict = nx.pagerank(G)
            except (ImportError, AttributeError) as e:
                print("Warning: SciPy-based PageRank failed, falling back to pure-Python pagerank:", e)
                cent_dict = _pagerank_python(
                    G,
                    alpha=0.85,
                    max_iter=100,
                    tol=1.0e-6,
                    nstart=None,
                    weight="weight",
                    dangling=None,
                )
        else:
            cent_dict = func(G)

        # group values by type
        vals = {t: [] for t in types}
        for nid, data in G.nodes(data=True):
            t = data.get("type", "").upper()
            if t in vals:
                vals[t].append(cent_dict.get(nid, 0.0))

        # for each type, build & plot histogram
        for t in types:
            arr = np.array(vals[t])
            if arr.size == 0:
                print(f"[{name} | {t}] no data, skipping.")
                continue

            counts, bin_edges = np.histogram(arr, bins=bins)

            # print histogram data
            print(f"\nHistogram data for {name.capitalize()} Centrality – {t}:")
            for i in range(len(counts)):
                print(f"  bin {i}: [{bin_edges[i]:.4f}, {bin_edges[i+1]:.4f}) → {counts[i]}")

            # plot
            plt.figure()
            centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            width = (bin_edges[1] - bin_edges[0]) * 0.9
            plt.bar(
                centers,
                counts,
                width=width,
                color=TYPE_COLORS[t],
                edgecolor="black",
            )
            plt.ylim(0, counts.max() + 50)
            plt.title(f"{name.capitalize()} Centrality: {t}")
            plt.xlabel(f"{name.capitalize()} Centrality")
            plt.ylabel("Number of Nodes")
            plt.tight_layout()

            fn = os.path.join(output_dir, f"{name}_{t.lower()}_histogram.png")
            plt.savefig(fn)
            plt.close()
            print(f"  → saved plot to {fn}")
            
def main():
    parser = argparse.ArgumentParser(
        description="Citation graph tool: build, revise, and draw graph from JSON files in directory."
    )
    parser.add_argument(
        "--directory",
        default="IDs",
        help="Directory containing JSON files (default: IDs)"
    )
    parser.add_argument(
        "--graph_output",
        default="graph_model.json",
        help="Filename for the built graph model (JSON)"
    )
    parser.add_argument(
        "--revised_output",
        default="revised_graph_model.json",
        help="Filename for the revised graph model (JSON)"
    )
    parser.add_argument(
        "--interactive_output",
        default="citation_network.html",
        help="Filename for the interactive graph HTML output"
    )
    parser.add_argument(
        "--skip_revise",
        action="store_true",
        help="Skip the graph revision step"
    )
    parser.add_argument(
        "--plot_dir", default="centrality_plots",
        help="Directory to save centrality histograms"
    )
    args = parser.parse_args()

    # Step 1: Build graph model
    print("Building graph model...")
    graph = process_folder(args.directory)
    with open(args.graph_output, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)
    print("Graph model written to {}".format(args.graph_output))

    # Step 2: Revise graph model
    if not args.skip_revise:
        print("\nRevising graph model...")
        graph = revise_graph_model(graph)
        with open(args.revised_output, "w", encoding="utf-8") as f:
            json.dump(graph, f, indent=2)
        print("Revised graph model written to {}".format(args.revised_output))

    # Step 3: Analyze and visualize
    print("\nAnalyzing graph...")
    analyze_graph(graph)
    
    print("Plotting centrality histograms...")
    plot_centrality_histograms(graph, output_dir=args.plot_dir)


    print("\nCreating interactive visualization...")
    draw_interactive_graph(graph, args.interactive_output)

if __name__ == "__main__":
    main()
