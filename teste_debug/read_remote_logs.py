import subprocess
import sys

def main():
    try:
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

        print("Obtendo logs do servidor remoto...")
        out = subprocess.check_output(
            'ssh hostinger-root "docker logs --tail 3000 smartcoreassistant_app"',
            shell=True,
            stderr=subprocess.STDOUT
        )
        print("Logs obtidos com sucesso. Filtrando e buscando erros/tracebacks...")
        lines = out.splitlines()
        
        output_lines = []
        in_traceback = False
        traceback_lines = []
        
        for line_bytes in lines:
            line = line_bytes.decode('utf-8', errors='ignore')
            
            # Se for uma linha que indica o começo de um Traceback
            if "Traceback (most recent call last)" in line:
                in_traceback = True
                traceback_lines = [line]
                continue
                
            if in_traceback:
                traceback_lines.append(line)
                if len(line) > 0 and not line.startswith(' ') and not line.startswith('\t'):
                    in_traceback = False
                    output_lines.append("\n" + "="*80)
                    output_lines.append("TRACEBACK DETECTADO:")
                    output_lines.append("="*80)
                    output_lines.extend(traceback_lines)
                    output_lines.append("="*80 + "\n")
                    traceback_lines = []
                continue
                
            # Captura qualquer linha com erro ou exceção
            if any(err in line for err in ["Exception", "Error", "500 Internal Server Error", "HTTP/1.1\" 500", "django.request"]):
                output_lines.append(f"LINHA DE INTERESSE: {line}")
                
        # Vamos também salvar os logs brutos para que possamos ler caso necessário
        with open("teste_debug/remote_logs_raw.txt", "w", encoding="utf-8") as f:
            for line_bytes in lines:
                f.write(line_bytes.decode('utf-8', errors='ignore') + "\n")
        print("Logs brutos salvos em teste_debug/remote_logs_raw.txt")

        if output_lines:
            print(f"Foram encontradas {len(output_lines)} linhas de erro/interesse:")
            for o_line in output_lines:
                try:
                    print(o_line)
                except Exception:
                    print(o_line.encode('ascii', errors='replace').decode('ascii'))
        else:
            print("Nenhum erro ou Traceback evidente encontrado.")
            
    except subprocess.CalledProcessError as e:
        print(f"Erro no comando ssh: {e.output.decode('utf-8', errors='ignore')}")
    except Exception as e:
        print(f"Erro inesperado no script: {e}")

if __name__ == "__main__":
    main()
