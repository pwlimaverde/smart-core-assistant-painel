import os

def update_docker_compose():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    project_name = os.path.basename(project_root)
    docker_compose_path = os.path.join(project_root, 'docker-compose.yml')
    
    docker_compose_content = f"""# Arquivo gerenciado pelo ambiente_misto
name: {project_name}

services:
  postgres:
    image: postgres:13
    container_name: postgres_db
    environment:
      POSTGRES_DB: ${{POSTGRES_DB:-smart_core_db}}
      POSTGRES_USER: ${{POSTGRES_USER:-postgres}}
      POSTGRES_PASSWORD: ${{POSTGRES_PASSWORD:-postgres123}}
    ports:
      - "${{POSTGRES_PORT:-5434}}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

  redis:
    image: redis:6.2-alpine
    container_name: redis_cache
    ports:
      - "${{REDIS_PORT:-6381}}:6379"
    networks:
      - app-network

volumes:
  postgres_data:

networks:
  app-network:
    driver: bridge
"""
    with open(docker_compose_path, 'w', encoding='utf-8') as f:
        f.write(docker_compose_content)
    print(f"'docker-compose.yml' atualizado com sucesso em: {docker_compose_path}")

if __name__ == "__main__":
    update_docker_compose()