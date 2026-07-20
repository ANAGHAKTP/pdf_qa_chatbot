"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Citation, ConfidenceReport } from "@/types/workspace";

export function useStreaming() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedText, setStreamedText] = useState("");
  const [streamedCitations, setStreamedCitations] = useState<Citation[]>([]);
  const [streamedConfidence, setStreamedConfidence] = useState<ConfidenceReport | null>(null);
  const [activeStage, setActiveStage] = useState<string | null>(null);
  const [streamedMetrics, setStreamedMetrics] = useState<any>(null);
  const [streamError, setStreamError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  const abortActiveStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsStreaming(false);
      setActiveStage(null);
      setStreamError("Streaming generation was stopped.");
    }
  }, []);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const startStream = useCallback(
    async (
      url: string,
      body: any,
      headers: Record<string, string> = {}
    ) => {
      // Abort any active streams first
      abortActiveStream();

      setIsStreaming(true);
      setStreamError(null);
      setStreamedText("");
      setStreamedCitations([]);
      setStreamedConfidence(null);
      setActiveStage("Analyzing Query...");
      setStreamedMetrics(null);

      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...headers,
          },
          body: JSON.stringify(body),
          signal: controller.signal,
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || "Query stream request failed");
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        if (!reader) {
          throw new Error("Response body is not readable");
        }

        let buffer = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line.startsWith("event:")) {
              const eventType = line.replace("event:", "").trim();
              const dataLine = lines[i + 1]?.trim() || "";
              if (dataLine.startsWith("data:")) {
                const rawData = dataLine.replace("data:", "").trim();
                i++; // Skip data line in loop

                if (eventType === "stage") {
                  try {
                    const stageObj = JSON.parse(rawData);
                    setActiveStage(stageObj.stage);
                  } catch (e) {}
                } else if (eventType === "citations") {
                  try {
                    const parsedCitations = JSON.parse(rawData);
                    setStreamedCitations(parsedCitations);
                  } catch (e) {
                    console.error("Failed to parse citations:", e);
                  }
                } else if (eventType === "confidence") {
                  try {
                    const parsedConf = JSON.parse(rawData);
                    setStreamedConfidence(parsedConf);
                  } catch (e) {
                    console.error("Failed to parse confidence:", e);
                  }
                } else if (eventType === "message") {
                  try {
                    const parsed = JSON.parse(rawData);
                    setStreamedText((prev) => prev + parsed.chunk);
                  } catch (e) {
                    console.error("Failed to parse message chunk:", e);
                  }
                } else if (eventType === "metrics") {
                  try {
                    const parsedMetrics = JSON.parse(rawData);
                    setStreamedMetrics(parsedMetrics);
                  } catch (e) {
                    console.error("Failed to parse metrics:", e);
                  }
                } else if (eventType === "error") {
                  try {
                    const parsed = JSON.parse(rawData);
                    throw new Error(parsed.detail || "Streaming error encountered");
                  } catch (e: any) {
                    throw new Error(e.message || "Streaming error encountered");
                  }
                } else if (eventType === "close") {
                  setIsStreaming(false);
                  setActiveStage(null);
                  abortControllerRef.current = null;
                  return;
                }
              }
            }
          }
        }
      } catch (err: any) {
        if (err.name === "AbortError") {
          console.log("Stream aborted by user");
        } else {
          console.error("Streaming failed:", err);
          setStreamError(err.message || "Failed to retrieve response streaming chunks.");
        }
      } finally {
        setIsStreaming(false);
        setActiveStage(null);
        abortControllerRef.current = null;
      }
    },
    [abortActiveStream]
  );

  return {
    isStreaming,
    streamedText,
    streamedCitations,
    streamedConfidence,
    activeStage,
    streamedMetrics,
    streamError,
    setStreamError,
    startStream,
    abortActiveStream,
  };
}
