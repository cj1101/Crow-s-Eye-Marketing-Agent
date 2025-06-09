#!/usr/bin/env python3
"""
Crow's Eye Marketing Agent - Web App Installer
Updated version with API integration and enhanced features
"""

import subprocess
import sys
import os
import json
from pathlib import Path
import shutil

def print_banner(message, char="="):
    """Print a banner message"""
    print()
    print(char * 60)
    print(f" {message}")
    print(char * 60)

def run_command(command, description=None, cwd=None):
    """Run a command and handle errors"""
    if description:
        print(f"🔧 {description}...")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, cwd=cwd)
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"   Details: {e.stderr.strip()}")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    dependencies = {
        "node": "Node.js",
        "npm": "npm",
        "python": "Python 3",
        "git": "Git"
    }
    
    missing = []
    for cmd, name in dependencies.items():
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            print(f"✅ {name} is installed")
        except:
            print(f"❌ {name} is not installed")
            missing.append(name)
    
    return len(missing) == 0

def create_web_app_structure():
    """Create the web app directory structure"""
    web_app_dir = Path("web_app")
    
    # Create main directories
    directories = [
        "web_app/src",
        "web_app/src/components",
        "web_app/src/components/Media",
        "web_app/src/components/Posts",
        "web_app/src/components/AI",
        "web_app/src/components/Analytics",
        "web_app/src/components/Dashboard",
        "web_app/src/pages",
        "web_app/src/services",
        "web_app/src/utils",
        "web_app/src/hooks",
        "web_app/src/context",
        "web_app/src/assets",
        "web_app/public",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Created web app directory structure")
    return web_app_dir

def create_package_json(web_app_dir):
    """Create package.json for the web app"""
    package_json = {
        "name": "crows-eye-marketing-agent",
        "version": "2.0.0",
        "description": "AI-powered social media marketing agent with comprehensive content management",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview",
            "lint": "eslint . --ext js,jsx,ts,tsx --report-unused-disable-directives --max-warnings 0",
            "type-check": "tsc --noEmit"
        },
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-router-dom": "^6.8.0",
            "axios": "^1.6.0",
            "lucide-react": "^0.294.0",
            "tailwindcss": "^3.3.6",
            "autoprefixer": "^10.4.16",
            "postcss": "^8.4.32",
            "@headlessui/react": "^1.7.17",
            "@heroicons/react": "^2.0.18",
            "framer-motion": "^10.16.16",
            "react-query": "^3.39.3",
            "zustand": "^4.4.7",
            "react-hook-form": "^7.48.2",
            "@hookform/resolvers": "^3.3.2",
            "zod": "^3.22.4",
            "react-dropzone": "^14.2.3",
            "react-hot-toast": "^2.4.1",
            "date-fns": "^2.30.0",
            "recharts": "^2.8.0",
            "react-markdown": "^9.0.1",
            "prismjs": "^1.29.0"
        },
        "devDependencies": {
            "@types/react": "^18.2.37",
            "@types/react-dom": "^18.2.15",
            "@vitejs/plugin-react": "^4.1.1",
            "typescript": "^5.2.2",
            "vite": "^5.0.0",
            "eslint": "^8.53.0",
            "@typescript-eslint/eslint-plugin": "^6.10.0",
            "@typescript-eslint/parser": "^6.10.0",
            "eslint-plugin-react-hooks": "^4.6.0",
            "eslint-plugin-react-refresh": "^0.4.4"
        }
    }
    
    package_file = web_app_dir / "package.json"
    with open(package_file, 'w') as f:
        json.dump(package_json, f, indent=2)
    
    print("✅ Created package.json")

def create_vite_config(web_app_dir):
    """Create Vite configuration"""
    vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: true
  }
})"""
    
    with open(web_app_dir / "vite.config.ts", 'w') as f:
        f.write(vite_config)
    
    print("✅ Created Vite configuration")

def create_tailwind_config(web_app_dir):
    """Create Tailwind CSS configuration"""
    tailwind_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}"""
    
    with open(web_app_dir / "tailwind.config.js", 'w') as f:
        f.write(tailwind_config)
    
    # Create PostCSS config
    postcss_config = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}"""
    
    with open(web_app_dir / "postcss.config.js", 'w') as f:
        f.write(postcss_config)
    
    print("✅ Created Tailwind CSS configuration")

def create_typescript_config(web_app_dir):
    """Create TypeScript configuration"""
    ts_config = {
        "compilerOptions": {
            "target": "ES2020",
            "useDefineForClassFields": True,
            "lib": ["ES2020", "DOM", "DOM.Iterable"],
            "module": "ESNext",
            "skipLibCheck": True,
            "moduleResolution": "bundler",
            "allowImportingTsExtensions": True,
            "resolveJsonModule": True,
            "isolatedModules": True,
            "noEmit": True,
            "jsx": "react-jsx",
            "strict": True,
            "noUnusedLocals": True,
            "noUnusedParameters": True,
            "noFallthroughCasesInSwitch": True,
            "baseUrl": "./src",
            "paths": {
                "@/*": ["*"],
                "@/components/*": ["components/*"],
                "@/services/*": ["services/*"],
                "@/utils/*": ["utils/*"],
                "@/hooks/*": ["hooks/*"],
                "@/context/*": ["context/*"]
            }
        },
        "include": ["src"],
        "references": [{"path": "./tsconfig.node.json"}]
    }
    
    with open(web_app_dir / "tsconfig.json", 'w') as f:
        json.dump(ts_config, f, indent=2)
    
    print("✅ Created TypeScript configuration")

def create_base_files(web_app_dir):
    """Create base HTML and CSS files"""
    # Create index.html
    index_html = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Crow's Eye Marketing Agent</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>"""
    
    with open(web_app_dir / "index.html", 'w') as f:
        f.write(index_html)
    
    # Create main CSS file
    main_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    font-family: 'Inter', system-ui, sans-serif;
  }
}

@layer components {
  .btn-primary {
    @apply bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200;
  }
  
  .btn-secondary {
    @apply bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 px-4 rounded-lg transition-colors duration-200;
  }
  
  .card {
    @apply bg-white rounded-lg shadow-sm border border-gray-200 p-6;
  }
  
  .input-field {
    @apply w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent;
  }
}"""
    
    with open(web_app_dir / "src" / "index.css", 'w') as f:
        f.write(main_css)
    
    print("✅ Created base HTML and CSS files")

def create_api_service(web_app_dir):
    """Create API service for connecting to the backend"""
    api_service = """import axios from 'axios';

// Configure axios defaults
const api = axios.create({
  baseURL: process.env.NODE_ENV === 'production' 
    ? 'https://your-project.uc.r.appspot.com' 
    : 'http://localhost:8000',
  timeout: 10000,
});

// Request interceptor for auth
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const apiService = {
  // Health checks
  checkHealth: () => api.get('/health'),
  checkApiHealth: () => api.get('/api/v1/health'),
  
  // Media endpoints
  uploadMedia: (formData: FormData) => api.post('/api/v1/media/upload', formData),
  getMedia: (params?: any) => api.get('/api/v1/media', { params }),
  deleteMedia: (mediaId: string) => api.delete(`/api/v1/media/${mediaId}`),
  
  // Posts endpoints
  createPost: (postData: any) => api.post('/api/v1/posts', postData),
  getPosts: (params?: any) => api.get('/api/v1/posts', { params }),
  updatePost: (postId: string, data: any) => api.put(`/api/v1/posts/${postId}`, data),
  deletePost: (postId: string) => api.delete(`/api/v1/posts/${postId}`),
  
  // AI endpoints
  generateCaption: (data: any) => api.post('/api/v1/ai/generate-caption', data),
  generateHighlight: (data: any) => api.post('/api/v1/ai/generate-highlight', data),
  optimizeContent: (data: any) => api.post('/api/v1/ai/optimize-content', data),
  
  // Analytics endpoints
  getAnalytics: (params?: any) => api.get('/api/v1/analytics', { params }),
  getPostAnalytics: (postId: string) => api.get(`/api/v1/analytics/posts/${postId}`),
  
  // Gallery endpoints
  createGallery: (data: any) => api.post('/api/v1/galleries', data),
  getGalleries: () => api.get('/api/v1/galleries'),
  
  // Context files
  uploadContextFile: (formData: FormData) => api.post('/api/v1/context-files', formData),
  getContextFiles: () => api.get('/api/v1/context-files'),
};

export default api;"""
    
    with open(web_app_dir / "src" / "services" / "api.ts", 'w') as f:
        f.write(api_service)
    
    print("✅ Created API service")

def install_web_app():
    """Main installation function"""
    print_banner("🦅 Crow's Eye Marketing Agent - Web App Installer v2.0", "🦅")
    
    print("📋 This installer will create a modern React web app with:")
    print("   • React 18 + TypeScript + Vite")
    print("   • Tailwind CSS for styling")
    print("   • API integration with the backend")
    print("   • AI-powered content management")
    print("   • Media processing and analytics")
    print("   • Modern UI components")
    print()
    
    # Check dependencies
    print_banner("🔍 Checking Dependencies")
    if not check_dependencies():
        print("❌ Please install missing dependencies and run this script again.")
        return False
    
    # Create web app structure
    print_banner("📁 Creating Web App Structure")
    web_app_dir = create_web_app_structure()
    
    # Create configuration files
    print_banner("⚙️ Creating Configuration Files")
    create_package_json(web_app_dir)
    create_vite_config(web_app_dir)
    create_tailwind_config(web_app_dir)
    create_typescript_config(web_app_dir)
    create_base_files(web_app_dir)
    create_api_service(web_app_dir)
    
    # Install dependencies
    print_banner("📦 Installing Dependencies")
    if run_command("npm install", "Installing Node.js dependencies", cwd=web_app_dir):
        print("✅ Dependencies installed successfully")
    else:
        print("❌ Failed to install dependencies")
        return False
    
    print_banner("🎉 Installation Complete!", "🎉")
    print("✅ Web app created successfully!")
    print()
    print("🚀 Next steps:")
    print(f"   1. cd {web_app_dir}")
    print("   2. npm run dev")
    print("   3. Open http://localhost:3000")
    print()
    print("🔧 Development commands:")
    print("   • npm run dev     - Start development server")
    print("   • npm run build   - Build for production")
    print("   • npm run preview - Preview production build")
    print()
    print("🌐 Make sure your API is running on http://localhost:8000")
    print("   Run: python start_api.py")
    
    return True

if __name__ == "__main__":
    success = install_web_app()
    sys.exit(0 if success else 1) 