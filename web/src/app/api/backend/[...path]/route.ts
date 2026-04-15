import { NextRequest, NextResponse } from "next/server";

const EMILY_BASE_URL = process.env.EMILY_API_URL || "http://localhost:8000";

async function proxy(request: NextRequest, path: string[]) {
  const target = `${EMILY_BASE_URL}/api/${path.join("/")}`;
  const authorization = request.headers.get("authorization");
  const contentType = request.headers.get("content-type");

  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  const body = hasBody ? await request.text() : undefined;

  const upstream = await fetch(target, {
    method: request.method,
    headers: {
      ...(contentType ? { "Content-Type": contentType } : {}),
      ...(authorization ? { Authorization: authorization } : {}),
    },
    body,
  });

  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") || "application/json",
    },
  });
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
