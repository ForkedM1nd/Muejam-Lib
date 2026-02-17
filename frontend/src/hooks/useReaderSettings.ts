import { useState, useCallback, useEffect } from "react";
import { DEFAULT_READER_SETTINGS, type ReaderSettings } from "@/types";

const STORAGE_KEY = "muejam-reader-settings";

export function useReaderSettings() {
  const [settings, setSettingsState] = useState<ReaderSettings>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? { ...DEFAULT_READER_SETTINGS, ...JSON.parse(stored) } : DEFAULT_READER_SETTINGS;
    } catch {
      return DEFAULT_READER_SETTINGS;
    }
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }, [settings]);

  const setSettings = useCallback((partial: Partial<ReaderSettings>) => {
    setSettingsState((prev) => ({ ...prev, ...partial }));
  }, []);

  const lineWidthPx = settings.lineWidth === "narrow" ? 560 : settings.lineWidth === "wide" ? 780 : 680;

  return { settings, setSettings, lineWidthPx };
}
