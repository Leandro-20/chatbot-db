#!/bin/bash
echo "Migrando datos a SQLite..."
python3 migrate.py
echo ""
echo "Creando modelo chatbot-db..."
ollama create chatbot-db -f Modelfile
echo ""
echo "Modelo creado! Ejecuta:"
echo "  python3 chat.py"
echo ""
echo "O corre los tests con:"
echo "  python3 test_db.py"
