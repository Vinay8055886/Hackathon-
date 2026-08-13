export { default } from "next-auth/middleware";

export const config = {
  // Protect everything except the login page, auth API, and static assets.
  matcher: ["/((?!login|api/auth|_next/static|_next/image|favicon.ico).*)"],
};
