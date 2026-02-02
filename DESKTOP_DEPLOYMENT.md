# Maxwell Desktop Deployment Strategy

**Last Updated:** 2026-02-02
**Status:** Planning → Implementation
**Owner:** Implementation Team

---

## Executive Summary

Maxwell was designed as a **local-first fiction writing IDE** with privacy as a core principle. While the architecture supports this vision (SQLite, local Git, BYOK AI), the implementation has been web-only. This document outlines the path to true desktop distribution.

### Current State vs. Vision

| Aspect | Original Vision | Current State | Gap |
|--------|----------------|---------------|-----|
| **Distribution** | Single installer | Two-process setup | Major |
| **Installation** | Download and run | Python + Node required | Major |
| **Privacy** | Fully local | Fully local | None |
| **Offline** | Works offline | Works offline | None |
| **Data Storage** | Local SQLite | Local SQLite | None |

**Bottom Line:** The architecture is sound. We need to package it properly.

---

## Distribution Strategy (Phased Approach)

### Phase D1: Self-Hosted Beta (Immediate - Week 1)
**Target:** Privacy-conscious early adopters who can run Docker

- Docker Compose setup for one-command deployment
- Works on Windows (WSL2), macOS, Linux
- All data stays on user's machine
- No cloud dependency

**Deliverables:**
- `docker-compose.yml` for full stack
- `Dockerfile` for backend
- `Dockerfile` for frontend
- Installation script (`install.sh` / `install.ps1`)
- Self-hosted documentation

### Phase D2: Electron Desktop App (Weeks 2-4)
**Target:** General users who want a native experience

- Single installer for Windows, macOS, Linux
- Backend embedded using PyInstaller
- Auto-start/stop backend with app lifecycle
- Native file dialogs for manuscript export
- System tray integration

**Deliverables:**
- Electron main process
- PyInstaller backend bundle
- Auto-updater integration
- Code signing setup
- Platform-specific installers

### Phase D3: Distribution & Updates (Weeks 5-6)
**Target:** Sustainable distribution infrastructure

- GitHub Releases for downloads
- Auto-update mechanism
- Crash reporting (opt-in)
- Usage analytics (opt-in, privacy-respecting)

---

## Phase D1: Self-Hosted Beta (Docker)

### Architecture

```
┌─────────────────────────────────────────────────┐
│                  Docker Host                     │
│  ┌──────────────┐    ┌────────────────────────┐ │
│  │   Frontend   │    │       Backend          │ │
│  │   (nginx)    │◄───┤    (FastAPI/uvicorn)   │ │
│  │   Port 80    │    │      Port 8000         │ │
│  └──────────────┘    └────────────────────────┘ │
│          │                      │               │
│          └──────────┬───────────┘               │
│                     ▼                           │
│          ┌────────────────────┐                 │
│          │   Shared Volume    │                 │
│          │   /data (SQLite)   │                 │
│          └────────────────────┘                 │
└─────────────────────────────────────────────────┘
```

### Files to Create

1. **`docker/Dockerfile.backend`** - Python backend image
2. **`docker/Dockerfile.frontend`** - React frontend with nginx
3. **`docker-compose.yml`** - Orchestration
4. **`docker/nginx.conf`** - Frontend proxy configuration
5. **`scripts/install.sh`** - Unix installation script
6. **`scripts/install.ps1`** - Windows installation script

### Usage

```bash
# Quick start (Unix/macOS/Linux)
curl -fsSL https://raw.githubusercontent.com/your-repo/maxwell/main/scripts/install.sh | bash

# Quick start (Windows PowerShell)
iwr -useb https://raw.githubusercontent.com/your-repo/maxwell/main/scripts/install.ps1 | iex

# Manual start
git clone https://github.com/your-repo/maxwell.git
cd maxwell
docker-compose up -d

# Access Maxwell
open http://localhost:3000
```

### Data Persistence

All user data stored in Docker volume:
- `maxwell_data:/app/data` - SQLite database + Git repositories
- Volume persists across container restarts
- Easy backup: `docker cp maxwell_backend:/app/data ./backup`

---

## Phase D2: Electron Desktop App

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Electron App                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │                  Main Process                        ││
│  │  ┌─────────────┐  ┌──────────────────────────────┐  ││
│  │  │   Backend   │  │        App Lifecycle         │  ││
│  │  │  Manager    │  │  - Window management         │  ││
│  │  │  (spawns    │  │  - Menu bar                  │  ││
│  │  │  PyInstaller│  │  - Auto-update               │  ││
│  │  │  bundle)    │  │  - Tray icon                 │  ││
│  │  └─────────────┘  └──────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────┐│
│  │                 Renderer Process                     ││
│  │  ┌─────────────────────────────────────────────────┐││
│  │  │              React Frontend                      │││
│  │  │  (Loaded from file:// or localhost)             │││
│  │  └─────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### Directory Structure

```
electron/
├── main/
│   ├── index.ts           # Main process entry
│   ├── backend-manager.ts # Start/stop Python backend
│   ├── menu.ts            # Application menu
│   ├── tray.ts            # System tray
│   └── updater.ts         # Auto-update logic
├── preload/
│   └── index.ts           # Preload script for IPC
├── resources/
│   └── icons/             # App icons (icns, ico, png)
├── scripts/
│   ├── build-backend.sh   # PyInstaller build script
│   └── notarize.js        # macOS notarization
└── electron-builder.yml   # Build configuration
```

### Backend Bundling (PyInstaller)

```python
# backend/maxwell.spec (PyInstaller spec file)
a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('app/nlp/models', 'app/nlp/models'),  # spaCy models
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.protocols.http',
        'sqlalchemy.dialects.sqlite',
    ],
    ...
)
```

### Platform-Specific Builds

| Platform | Format | Code Signing | Notarization |
|----------|--------|--------------|--------------|
| **macOS** | DMG, pkg | Apple Developer ID | Required |
| **Windows** | NSIS, MSI | EV Certificate | SmartScreen |
| **Linux** | AppImage, deb, rpm | GPG optional | N/A |

### Electron Dependencies

```json
{
  "devDependencies": {
    "electron": "^28.0.0",
    "electron-builder": "^24.0.0",
    "electron-updater": "^6.0.0",
    "@electron/notarize": "^2.0.0"
  }
}
```

---

## Phase D3: Distribution Infrastructure

### Download Channels

1. **GitHub Releases** (Primary)
   - Tagged releases with changelogs
   - Platform-specific assets
   - Checksums for verification

2. **Website** (maxwell.app)
   - Download buttons per platform
   - Auto-detect OS
   - Installation instructions

3. **Package Managers** (Future)
   - Homebrew Cask (macOS)
   - Chocolatey (Windows)
   - Flatpak/Snap (Linux)

### Auto-Update Strategy

```typescript
// electron/main/updater.ts
import { autoUpdater } from 'electron-updater';

autoUpdater.setFeedURL({
  provider: 'github',
  owner: 'your-org',
  repo: 'maxwell'
});

// Check for updates on startup (after 10 second delay)
setTimeout(() => autoUpdater.checkForUpdatesAndNotify(), 10000);
```

### Privacy-Respecting Analytics (Opt-In)

- PostHog self-hosted or privacy mode
- No PII collected
- Aggregated feature usage only
- Clear opt-out in settings

---

## Implementation Timeline

### Week 1: Docker Self-Hosted (Phase D1)
| Day | Task | Owner |
|-----|------|-------|
| Mon | Create Docker files | Dev |
| Tue | Test on Linux/macOS | Dev |
| Wed | Test on Windows (WSL2) | Dev |
| Thu | Write documentation | Dev |
| Fri | Beta user testing | Team |

### Weeks 2-3: Electron Foundation (Phase D2)
| Week | Task | Owner |
|------|------|-------|
| W2 Mon-Wed | Electron main process setup | Dev |
| W2 Thu-Fri | Backend manager (PyInstaller) | Dev |
| W3 Mon-Tue | Frontend integration | Dev |
| W3 Wed-Thu | Platform testing | Dev |
| W3 Fri | Bug fixes | Dev |

### Week 4: Electron Polish (Phase D2)
| Day | Task | Owner |
|-----|------|-------|
| Mon | Native file dialogs | Dev |
| Tue | System tray + menu | Dev |
| Wed | Auto-updater | Dev |
| Thu | Code signing setup | Dev |
| Fri | Build all platforms | Dev |

### Weeks 5-6: Distribution (Phase D3)
| Week | Task | Owner |
|------|------|-------|
| W5 | GitHub Releases workflow | Dev |
| W5 | macOS notarization | Dev |
| W6 | Windows SmartScreen | Dev |
| W6 | Documentation + landing page | Team |

---

## Technical Decisions

### ADR-D01: Electron over Tauri

**Decision:** Use Electron for desktop packaging

**Context:** Need to ship desktop app quickly with existing React frontend

**Options Considered:**
1. **Electron** - Chromium + Node.js, large bundle (~150MB)
2. **Tauri** - System WebView + Rust, smaller bundle (~20MB)
3. **Neutralino** - Lightweight alternative, limited features

**Decision Rationale:**
- Electron has mature ecosystem (electron-builder, auto-updater)
- Team familiar with JavaScript/TypeScript
- Tauri would require Rust knowledge for backend embedding
- Bundle size acceptable for desktop app
- Faster time to market (3-4 weeks vs 5-6 weeks)

**Consequences:**
- Larger download size (acceptable)
- Higher memory usage (acceptable for target audience)
- Well-documented path for future features

---

### ADR-D02: PyInstaller for Backend Bundling

**Decision:** Use PyInstaller to bundle Python backend

**Context:** Need to embed FastAPI backend in Electron app

**Options Considered:**
1. **PyInstaller** - Mature, well-documented
2. **cx_Freeze** - Alternative, less documentation
3. **Nuitka** - Compiles to C, complex setup
4. **Embedded Python** - Ship Python interpreter, complex

**Decision Rationale:**
- PyInstaller handles SQLAlchemy, FastAPI, spaCy well
- One-file mode simplifies distribution
- Large community and troubleshooting resources
- Works on all target platforms

**Consequences:**
- Bundle includes Python runtime (~50MB)
- First startup may be slower (extraction)
- Need to handle hidden imports carefully

---

### ADR-D03: Docker for Self-Hosted Beta

**Decision:** Provide Docker Compose as primary self-hosted option

**Context:** Need quick solution for privacy-conscious beta users

**Options Considered:**
1. **Docker Compose** - Standard, works everywhere
2. **Native installers** - Complex, platform-specific
3. **Virtual machine image** - Large, slow

**Decision Rationale:**
- Docker provides consistent environment
- Works on Windows (WSL2), macOS, Linux
- Easy to update (docker-compose pull)
- Data persistence via volumes
- Familiar to technical early adopters

**Consequences:**
- Requires Docker knowledge
- Not suitable for non-technical users
- Electron app will be primary for general users

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| PyInstaller bundle too large | Medium | Low | Accept 150MB, optimize later |
| macOS notarization fails | Medium | High | Test early, budget time |
| Windows SmartScreen warnings | High | Medium | Get EV certificate |
| Backend startup slow | Medium | Medium | Show loading screen |
| spaCy models missing | Low | High | Test bundling thoroughly |
| Auto-update breaks app | Low | Critical | Staged rollouts, rollback |

---

## Success Metrics

### Phase D1 (Docker)
- [ ] 50+ beta users running self-hosted
- [ ] <5 minute setup time
- [ ] Zero data loss incidents
- [ ] 90% positive feedback on privacy

### Phase D2 (Electron)
- [ ] Download size <200MB
- [ ] Cold start <10 seconds
- [ ] Works offline completely
- [ ] Auto-update works reliably

### Phase D3 (Distribution)
- [ ] 500+ downloads in first month
- [ ] <2% crash rate
- [ ] 4+ star average rating
- [ ] 80% retention after 30 days

---

## Appendix: Commands Reference

### Docker Commands

```bash
# Start Maxwell
docker-compose up -d

# Stop Maxwell
docker-compose down

# View logs
docker-compose logs -f

# Backup data
docker cp maxwell_backend:/app/data ./maxwell-backup-$(date +%Y%m%d)

# Restore data
docker cp ./maxwell-backup-20260202 maxwell_backend:/app/data

# Update to latest version
docker-compose pull && docker-compose up -d
```

### Electron Development Commands

```bash
# Install dependencies
cd electron && npm install

# Development mode
npm run dev

# Build for current platform
npm run build

# Build for all platforms
npm run build:all

# Build backend bundle
npm run build:backend
```

### PyInstaller Commands

```bash
# Create backend bundle
cd backend
pyinstaller maxwell.spec --clean

# Test bundle
./dist/maxwell/maxwell

# Check bundle size
du -sh dist/maxwell/
```

---

## Related Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
- [IMPLEMENTATION_PLAN_v2.md](./IMPLEMENTATION_PLAN_v2.md) - Development roadmap
- [PROGRESS.md](./PROGRESS.md) - Current progress
- [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - Development commands

---

**Document History:**
- 2026-02-02: Initial creation (desktop strategy planning)
