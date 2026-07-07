/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_ANALYTICS_ENABLED: string
  readonly VITE_AMAP_KEY: string
  readonly VITE_AMAP_SECURITY_JS_CODE: string
  readonly VITE_SENTRY_DSN: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
