import { NextRequest, NextResponse } from "next/server";

const EMILY_BASE_URL = process.env.EMILY_API_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.text();
    const authorization = request.headers.get("authorization");

    const response = await fetch(`${EMILY_BASE_URL}/api/pipeline/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(authorization ? { Authorization: authorization } : {}),
      },
      body,
    });

    const text = await response.text();
    return new NextResponse(text, {
      status: response.status,
      headers: { "Content-Type": response.headers.get("content-type") || "application/json" },
    });
  } catch (error) {
    return NextResponse.json({ detail: "Proxy analyze failed", error: String(error) }, { status: 502 });
  }
}
