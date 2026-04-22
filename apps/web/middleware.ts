import { NextRequest, NextResponse } from "next/server";
import { jwtVerify } from "jose";

const ACCESS_COOKIE = "onx_access_token";

async function isAccessTokenValid(token: string): Promise<boolean> {
  const secret = process.env.SECRET_KEY;
  if (!secret) return false;

  try {
    await jwtVerify(token, new TextEncoder().encode(secret), {
      algorithms: [process.env.ALGORITHM || "HS256"],
    });
    return true;
  } catch {
    return false;
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const accessToken = request.cookies.get(ACCESS_COOKIE)?.value;
  const isDashboardRoute = pathname.startsWith("/dashboard");
  const isLoginRoute = pathname === "/login";

  const validSession = accessToken ? await isAccessTokenValid(accessToken) : false;

  if (isDashboardRoute && !validSession) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (isLoginRoute && validSession) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/login"],
};
