# 📱 Sistema de Reparos — App Mobile (Flet)

App Android nativo com banco SQLite local no tablet.  
O APK é compilado **gratuitamente na nuvem** pelo GitHub Actions.

---

## 🚀 PASSO A PASSO — Do zero ao APK instalado

### PASSO 1 — Subir o código no GitHub

1. Acesse [github.com](https://github.com) e faça login
2. Clique em **"New repository"** (botão verde)
3. Dê o nome: `reparos-mobile`
4. Marque **Private** (privado)
5. Clique em **"Create repository"**

Agora, no PC, abra o **Prompt de Comando** (cmd) na pasta `tuinha_flet` e rode:

```bash
git init
git add .
git commit -m "versão inicial"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/reparos-mobile.git
git push -u origin main
```

> Substitua `SEU_USUARIO` pelo seu usuário do GitHub.

---

### PASSO 2 — Aguardar a compilação (≈ 10 minutos)

1. Acesse seu repositório no GitHub
2. Clique na aba **"Actions"**
3. Você verá o workflow **"Build APK Android"** rodando (ícone laranja girando)
4. Aguarde ficar verde ✅

---

### PASSO 3 — Baixar o APK

1. Clique no workflow concluído (✅ Build APK Android)
2. Role a página até **"Artifacts"**
3. Clique em **"reparos-apk"** para baixar o ZIP
4. Extraia o ZIP — dentro estará o arquivo `.apk`

---

### PASSO 4 — Instalar no tablet

1. Copie o `.apk` para o tablet (via cabo USB, WhatsApp, e-mail ou Google Drive)
2. No tablet, abra o arquivo `.apk`
3. Se aparecer aviso de segurança:
   - Vá em **Configurações → Segurança → Fontes desconhecidas** → Ativar
   - Ou toque em **"Instalar mesmo assim"**
4. Instale e abra o app!

---

### PASSO 5 — Primeira configuração no tablet

1. Abra o app — aparece a tela de login
2. Toque em **"Cadastrar Novo Usuário"**
3. Informe a senha do administrador: `#Val1001`
4. Crie seu usuário
5. Faça login e comece a usar!

---

## 🔄 Como atualizar o app

Sempre que quiser atualizar:

```bash
git add .
git commit -m "atualização"
git push
```

O GitHub Actions gera um novo APK automaticamente. Baixe e instale por cima do anterior.

---

## 📂 Sincronização com o PC

O banco do tablet fica em: `/data/data/br.marica.reparos/files/reparos.db`

Para sincronizar com o PC:
1. Conecte o tablet via USB
2. Use o **File Manager** do tablet para copiar o `.db`
3. O schema é compatível com o `SOLICITACOES.db` do sistema desktop

---

## 📁 Estrutura do projeto

```
tuinha_flet/
├── main.py                          ← App Flet completo
├── pyproject.toml                   ← Configurações do build
├── requirements.txt                 ← Dependências
├── README.md                        ← Este arquivo
└── .github/
    └── workflows/
        └── build-apk.yml            ← GitHub Actions (compilação automática)
```

---

## ✅ Funcionalidades do app mobile

- 🔐 Login com usuários cadastrados
- 📋 Lista de solicitações com busca e filtros (núcleo, situação)
- ➕ Criar nova solicitação com todos os campos
- ✏️ Editar solicitação existente
- 🧱 Gerenciar materiais por solicitação
- 📋 Histórico de alterações
- 💾 Banco SQLite local (funciona offline)
- 🔄 Info de sincronização com o PC

---

**Desenvolvido por Valdemir Vieira Alves — (21) 99431-3049**
