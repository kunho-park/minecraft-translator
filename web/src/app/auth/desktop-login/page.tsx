"use client";

import { useSession, signIn } from "next-auth/react";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";

type Status = "loading" | "need-login" | "generating" | "success" | "error";

function DesktopLoginInner() {
  const { data: session, status: sessionStatus } = useSession();
  const searchParams = useSearchParams();
  const port = searchParams.get("port");

  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState("");
  const triggered = useRef(false);

  const generateTokenAndRedirect = useCallback(async () => {
    if (!port || !session?.user) return;
    if (triggered.current) return;
    triggered.current = true;

    setStatus("generating");
    try {
      const res = await fetch("/api/auth/desktop-token", { method: "POST" });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || `HTTP ${res.status}`);
      }
      const { token, user } = await res.json();
      setStatus("success");

      const params = new URLSearchParams({
        token,
        name: user.name,
        discord_id: user.discordId,
      });
      window.location.href = `http://localhost:${port}/callback?${params}`;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setStatus("error");
    }
  }, [port, session]);

  useEffect(() => {
    if (sessionStatus === "loading") return;

    if (!port) {
      setError("Missing port parameter");
      setStatus("error");
      return;
    }

    if (sessionStatus === "unauthenticated") {
      setStatus("need-login");
      return;
    }

    if (sessionStatus === "authenticated" && session?.user) {
      generateTokenAndRedirect();
    }
  }, [sessionStatus, session, port, generateTokenAndRedirect]);

  const handleLogin = () => {
    signIn("discord", {
      callbackUrl: `/auth/desktop-login?port=${port}`,
    });
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#0a0a0a",
        color: "#fff",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <div
        style={{
          textAlign: "center",
          maxWidth: 420,
          padding: 40,
          borderRadius: 12,
          background: "#1a1a1a",
          border: "1px solid #333",
        }}
      >
        <h1 style={{ fontSize: 22, fontWeight: 600, marginBottom: 8 }}>
          데스크톱 앱 로그인
        </h1>
        <p style={{ color: "#888", fontSize: 14, marginBottom: 28 }}>
          모드팩 번역기 앱과 계정을 연결합니다
        </p>

        {status === "loading" && <p style={{ color: "#aaa" }}>로딩 중...</p>}

        {status === "need-login" && (
          <>
            <p style={{ color: "#ccc", marginBottom: 20, fontSize: 14 }}>
              Discord로 로그인하면 번역 업로드가 계정에 연결됩니다.
            </p>
            <button
              onClick={handleLogin}
              style={{
                background: "#5865F2",
                color: "#fff",
                border: "none",
                padding: "12px 32px",
                borderRadius: 8,
                fontSize: 15,
                fontWeight: 500,
                cursor: "pointer",
              }}
            >
              Discord로 로그인
            </button>
          </>
        )}

        {status === "generating" && (
          <p style={{ color: "#aaa" }}>토큰 생성 중...</p>
        )}

        {status === "success" && (
          <div>
            <p style={{ color: "#4ade80", marginBottom: 12 }}>
              로그인 완료! 앱으로 돌아가주세요.
            </p>
            <p style={{ color: "#888", fontSize: 13 }}>
              이 창은 닫아도 됩니다.
            </p>
          </div>
        )}

        {status === "error" && (
          <div>
            <p style={{ color: "#f87171", marginBottom: 12 }}>
              오류가 발생했습니다
            </p>
            <p style={{ color: "#888", fontSize: 13 }}>{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function DesktopLoginPage() {
  return (
    <Suspense
      fallback={
        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "#0a0a0a",
            color: "#aaa",
          }}
        >
          로딩 중...
        </div>
      }
    >
      <DesktopLoginInner />
    </Suspense>
  );
}
