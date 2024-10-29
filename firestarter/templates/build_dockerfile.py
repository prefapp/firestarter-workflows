from jinja2 import Environment, FileSystemLoader

file_loader = FileSystemLoader('/home/julian/Documentos/firestarter-workflows/firestarter/templates')
env = Environment(loader=file_loader)

def render_and_save_template(template_name, context, output_file):
    template = env.get_template(template_name)
    rendered_content = template.render(context)

    with open(output_file, 'w') as file:
        file.write(rendered_content)
    print(f"Dockerfile generado: {output_file}")

context_spa = {
    "fs_builder": {
        "technology": "spa-node:18-rev23",
        "template": "spa-rev3",
        "template_args": {"REWRITE_RULES": {}},
        "extra_packages": ["git"],
        "build_commands": ["npm ci", "npm run build"],
        "build_args": ["VITE_API_URL=https://my-url"]
    }
}

context_node_api = {
    "fs_builder": {
        "technology": "node:18-rev23",
        "template": "api-rev3",
        "extra_packages": ["curl"],
        "build_commands": ["npm ci", "npm run build"],
        "build_args": ["API_URL=https://api-url"]
    }
}

render_and_save_template("spa_template.j2", context_spa, "Dockerfile.spa")
render_and_save_template("node_api_template.j2", context_node_api, "Dockerfile.node")
