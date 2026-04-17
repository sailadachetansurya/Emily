import { NextRequest, NextResponse } from "next/server";

const EMILY_BASE_URL = process.env.EMILY_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function proxy(request: NextRequest, path: string[]) {
  const target = `${EMILY_BASE_URL}/api/${path.join("/")}`;
  const authorization = request.headers.get("authorization");
  const contentType = request.headers.get("content-type");

  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  const body = hasBody ? await request.text() : undefined;

  try {
    const upstream = await fetch(target, {
      method: request.method,
      headers: {
        ...(contentType ? { "Content-Type": contentType } : {}),
        ...(authorization ? { Authorization: authorization } : {}),
      },
      body,
      cache: 'no-store',
    });

    const text = await upstream.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }

    return NextResponse.json(data, {
      status: upstream.status,
    });
  } catch (error) {
    console.error("Proxy error:", error);
    return NextResponse.json(
      { 
        error: "Backend Unreachable", 
        detail: error instanceof Error ? error.message : String(error),
        target: target 
      },
      { status: 504 }
    );
  }
}

function getPath(request: NextRequest): string[] {
  const url = new URL(request.url);
  const parts = url.pathname.split("/").filter(Boolean);
  const index = parts.findIndex((p) => p === "backend");
  return index >= 0 ? parts.slice(index + 1) : [];
}

export async function GET(request: NextRequest) {
  return proxy(request, getPath(request));
}

export async function POST(request: NextRequest) {
  return proxy(request, getPath(request));
}

export async function PUT(request: NextRequest) {
  return proxy(request, getPath(request));
}

export async function DELETE(request: NextRequest) {
  return proxy(request, getPath(request));
}
