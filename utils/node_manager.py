import oxyapi
import dearpygui.dearpygui as dpg

"""Это ИИ пиздец простите (он не ворк)"""

class Connection:
    def __init__(self, link_id, in_attr, out_attr, in_node, out_node):
        self.link_id = link_id
        self.in_attr = in_attr
        self.out_attr = out_attr
        self.in_node = in_node  # Should be a single OxyNode instance
        self.out_node = out_node  # Should be a single OxyNode instance

class NodeManager:
    def __init__(self):
        self.connections: list[Connection] = []
    
    def add_connection(self, connection: Connection):
        self.connections.append(connection)

    def delete_connection(self, link_id):
        self.connections = [c for c in self.connections if c.link_id != link_id]

    def compile(self) -> str:
        # Collect all nodes involved in connections
        nodes = set()
        for conn in self.connections:
            if conn.in_node is not None:
                nodes.add(conn.in_node)
            if conn.out_node is not None:
                nodes.add(conn.out_node)
        nodes = list(nodes)

        # Build dependency graph and in-degree
        dependencies = {}
        in_degree = {}
        
        # Track each node instance separately
        for conn in self.connections:
            out_node = conn.out_node
            in_node = conn.in_node
            
            if out_node not in dependencies:
                dependencies[out_node] = []
            dependencies[out_node].append(in_node)
            
            in_degree[in_node] = in_degree.get(in_node, 0) + 1
            if out_node not in in_degree:
                in_degree[out_node] = 0
        # Topological sort using Kahn's algorithm
        queue = [node for node in nodes if in_degree[node] == 0]
        sorted_nodes = []
        while queue:
            node = queue.pop(0)
            sorted_nodes.append(node)
            for dependent in dependencies.get(node, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(sorted_nodes) != len(nodes):
            return "Error: Cyclic graph detected!"

        # Generate code
        code = []
        var_map = {}  # Maps node to variable name
        for i, node in enumerate(sorted_nodes):
            var_name = f"node{i}"
            var_map[node] = var_name

            # Collect inputs based on connections
            inputs = []
            input_attrs = [attr for attr in node.attrs if attr.type == dpg.mvNode_Attr_Input]
            for attr in input_attrs:
                for conn in self.connections:
                    if conn.in_node == node and conn.in_attr == attr.name:
                        source_var = var_map[conn.out_node]
                        output_idx = [a.name for a in conn.out_node.attrs if a.type == dpg.mvNode_Attr_Output].index(conn.out_attr)
                        inputs.append(f"{source_var}_output[{output_idx}]")
                        break
                else:
                    inputs.append("None")

            # Generate code line
            args = ", ".join(inputs)
            code_line = f"{var_name}_output = {node.__class__.__name__}.call({args})"
            code.append(code_line)

        return "\n".join(code)