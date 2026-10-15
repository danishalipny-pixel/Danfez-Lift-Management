from typing import Dict, Any, Optional
import httpx
from fastapi import HTTPException, status
from ..config import settings

class GoogleOAuthService:
    @property
    def is_configured(self) -> bool:
        return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_ID.strip())

    async def verify_google_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify Google OpenID Connect / OAuth 2.0 ID Token.
        """
        if not self.is_configured:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Google Sign-In is not configured on this server. Please provide GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in environment variables."
            )

        if not id_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google credential token is missing"
            )

        # Query Google's tokeninfo endpoint
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or expired Google credential"
                    )
                payload = resp.json()

                # Verify audience matches configured client ID if specified
                aud = payload.get("aud")
                if settings.GOOGLE_CLIENT_ID and aud != settings.GOOGLE_CLIENT_ID:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Google token audience does not match configured application client ID"
                    )

                return {
                    "email": payload.get("email"),
                    "name": payload.get("name", "Google User"),
                    "google_id": payload.get("sub"),
                    "avatar_url": payload.get("picture"),
                    "email_verified": payload.get("email_verified", True)
                }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Unable to communicate with Google authentication services: {str(e)}"
            )

google_oauth = GoogleOAuthService()
