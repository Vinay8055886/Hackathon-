import { DefaultSession } from "next-auth";
import { Role } from "@/lib/store/use-ui-store";

declare module "next-auth" {
  interface User {
    role?: Role;
    accessToken?: string;
  }

  interface Session {
    accessToken?: string;
    user: {
      id?: string;
      role?: Role;
    } & DefaultSession["user"];
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    role?: Role;
    accessToken?: string;
  }
}
