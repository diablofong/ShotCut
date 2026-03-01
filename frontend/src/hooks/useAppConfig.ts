import { useEffect, useState } from 'react';
import api from '../services/api';

export interface AppFeatures {
  clips: boolean;
  highlights: boolean;
  sharing: boolean;
}

interface AppConfig {
  features: AppFeatures;
}

const DEFAULT_FEATURES: AppFeatures = {
  clips: true,
  highlights: true,
  sharing: true,
};

let cachedConfig: AppConfig | null = null;

export function useAppConfig() {
  const [features, setFeatures] = useState<AppFeatures>(
    cachedConfig?.features ?? DEFAULT_FEATURES,
  );
  const [loading, setLoading] = useState(!cachedConfig);

  useEffect(() => {
    if (cachedConfig) return;
    api
      .get<AppConfig>('/config')
      .then((res) => {
        cachedConfig = res.data;
        setFeatures(res.data.features);
      })
      .catch(() => {
        // fallback to defaults on error
      })
      .finally(() => setLoading(false));
  }, []);

  return { features, loading };
}
