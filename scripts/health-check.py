#!/usr/bin/env python3
"""
Script de health check para os serviços Docker.
Verifica se todos os serviços estão funcionando corretamente.
"""

import sys
import time
import requests
import subprocess
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ServiceCheck:
    """Configuração de verificação de um serviço."""
    name: str
    url: str
    expected_status: int = 200
    timeout: int = 10
    required: bool = True


class HealthChecker:
    """Classe para verificar a saúde dos serviços."""
    
    def __init__(self):
        self.services = [
            ServiceCheck(
                name="Django Application",
                url="http://localhost:8000/admin/login/",
                expected_status=200
            ),
            ServiceCheck(
                name="Evolution API",
                url="http://localhost:8080/manager",
                expected_status=200
            ),
            ServiceCheck(
                name="MongoDB Express",
                url="http://localhost:8081",
                expected_status=200,
                required=False
            ),
            ServiceCheck(
                name="Redis Commander",
                url="http://localhost:8082",
                expected_status=200,
                required=False
            )
        ]
    
    def check_service(self, service: ServiceCheck) -> Tuple[bool, str]:
        """Verifica um serviço específico.
        
        Args:
            service: Configuração do serviço a ser verificado
            
        Returns:
            Tupla com (sucesso, mensagem)
        """
        try:
            response = requests.get(
                service.url,
                timeout=service.timeout,
                allow_redirects=True
            )
            
            if response.status_code == service.expected_status:
                return True, f"✅ {service.name}: OK"
            else:
                return False, f"❌ {service.name}: Status {response.status_code} (esperado {service.expected_status})"
                
        except requests.exceptions.ConnectionError:
            return False, f"❌ {service.name}: Conexão recusada"
        except requests.exceptions.Timeout:
            return False, f"❌ {service.name}: Timeout ({service.timeout}s)"
        except Exception as e:
            return False, f"❌ {service.name}: Erro - {str(e)}"
    
    def check_docker_containers(self) -> List[Tuple[bool, str]]:
        """Verifica o status dos containers Docker.
        
        Returns:
            Lista de tuplas com (sucesso, mensagem)
        """
        results = []
        
        try:
            # Verificar se Docker está rodando
            subprocess.run(
                ["docker", "version"],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Listar containers
            result = subprocess.run(
                ["docker-compose", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout.strip():
                results.append((True, "✅ Docker Compose: Containers encontrados"))
                
                # Verificar containers específicos
                expected_containers = [
                    "django-app",
                    "django-qcluster", 
                    "evolution-api",
                    "mongodb",
                    "redis"
                ]
                
                for container in expected_containers:
                    container_result = subprocess.run(
                        ["docker-compose", "ps", "-q", container],
                        capture_output=True,
                        text=True
                    )
                    
                    if container_result.stdout.strip():
                        # Verificar se está rodando
                        status_result = subprocess.run(
                            ["docker", "inspect", "-f", "{{.State.Status}}", container_result.stdout.strip()],
                            capture_output=True,
                            text=True
                        )
                        
                        if status_result.stdout.strip() == "running":
                            results.append((True, f"✅ Container {container}: Rodando"))
                        else:
                            results.append((False, f"❌ Container {container}: {status_result.stdout.strip()}"))
                    else:
                        results.append((False, f"❌ Container {container}: Não encontrado"))
            else:
                results.append((False, "❌ Docker Compose: Nenhum container encontrado"))
                
        except subprocess.CalledProcessError as e:
            results.append((False, f"❌ Docker: Erro ao verificar containers - {e}"))
        except FileNotFoundError:
            results.append((False, "❌ Docker: Comando não encontrado"))
            
        return results
    
    def run_health_check(self, verbose: bool = True) -> bool:
        """Executa verificação completa de saúde.
        
        Args:
            verbose: Se deve imprimir detalhes
            
        Returns:
            True se todos os serviços obrigatórios estão OK
        """
        if verbose:
            print("🏥 Verificação de Saúde dos Serviços")
            print("===================================\n")
        
        all_ok = True
        
        # Verificar containers Docker
        if verbose:
            print("🐳 Verificando containers Docker...")
        
        docker_results = self.check_docker_containers()
        for success, message in docker_results:
            if verbose:
                print(f"   {message}")
            if not success:
                all_ok = False
        
        if verbose:
            print("\n🌐 Verificando serviços web...")
        
        # Verificar serviços web
        for service in self.services:
            success, message = self.check_service(service)
            
            if verbose:
                print(f"   {message}")
            
            if not success and service.required:
                all_ok = False
        
        if verbose:
            print("\n" + "="*50)
            if all_ok:
                print("🎉 Todos os serviços obrigatórios estão funcionando!")
            else:
                print("⚠️  Alguns serviços apresentam problemas.")
        
        return all_ok
    
    def wait_for_services(self, max_wait: int = 300, check_interval: int = 10) -> bool:
        """Aguarda todos os serviços ficarem prontos.
        
        Args:
            max_wait: Tempo máximo de espera em segundos
            check_interval: Intervalo entre verificações em segundos
            
        Returns:
            True se todos os serviços ficaram prontos
        """
        print(f"⏳ Aguardando serviços ficarem prontos (máximo {max_wait}s)...")
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if self.run_health_check(verbose=False):
                elapsed = int(time.time() - start_time)
                print(f"✅ Todos os serviços prontos em {elapsed}s!")
                return True
            
            print(f"⏳ Aguardando... ({int(time.time() - start_time)}s)")
            time.sleep(check_interval)
        
        print(f"❌ Timeout: Serviços não ficaram prontos em {max_wait}s")
        return False


def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Health check para serviços Docker"
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Aguarda serviços ficarem prontos"
    )
    parser.add_argument(
        "--max-wait",
        type=int,
        default=300,
        help="Tempo máximo de espera em segundos (padrão: 300)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Modo silencioso (apenas código de saída)"
    )
    
    args = parser.parse_args()
    
    checker = HealthChecker()
    
    if args.wait:
        success = checker.wait_for_services(max_wait=args.max_wait)
    else:
        success = checker.run_health_check(verbose=not args.quiet)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()