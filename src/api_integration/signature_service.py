"""
Electronic Signature Service Implementation
Supports Mock DocuSign (free, simulated) and Real DocuSign API
"""

import os
import json
import uuid
import time
import shutil
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

import yaml

from .base import BaseSignatureService

# Import DocuSign SDK (only if using real DocuSign)
try:
    from docusign_esign import ApiClient, EnvelopesApi, EnvelopeDefinition, Document, Signer, \
        CarbonCopy, SignHere, Tabs, Recipients
    from docusign_esign.client.api_exception import ApiException
    DOCUSIGN_AVAILABLE = True
except ImportError:
    DOCUSIGN_AVAILABLE = False

# Import PandaDoc SDK (only if using PandaDoc)
try:
    import pandadoc_client
    from pandadoc_client import ApiClient as PandaDocApiClient, ApiException as PandaDocApiException
    from pandadoc_client.api import documents_api
    from pandadoc_client.model.document_create_request import DocumentCreateRequest
    from pandadoc_client.model.document_create_request_recipients import DocumentCreateRequestRecipients
    from pandadoc_client.model.document_send_request import DocumentSendRequest
    PANDADOC_AVAILABLE = True
except ImportError:
    PANDADOC_AVAILABLE = False


class MockDocuSignService(BaseSignatureService):
    """Mock DocuSign electronic signature service"""

    def __init__(self, config_path: str = "config/api_config.yaml"):
        """
        Initialize Mock DocuSign service

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()

        # Get Mock DocuSign configuration
        signature_config = self.config.get('signature_service', {})
        mock_config = signature_config.get('mock_docusign', {})

        self.output_dir = Path(mock_config.get('output_dir', 'collected_data/signatures'))
        self.simulate_delay = mock_config.get('simulate_delay_seconds', 2)
        self.default_signer_name = mock_config.get('default_signer_name', 'Test Signer')
        self.default_signer_email = self._resolve_env_var(
            mock_config.get('default_signer_email', 'signer@example.com')
        )

        # Settings
        settings = signature_config.get('settings', {})
        self.retry_attempts = settings.get('retry_attempts', 3)
        self.timeout = settings.get('timeout_seconds', 30)
        self.generate_pdf = settings.get('generate_pdf', True)

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # In-memory storage for envelope status (would be database in real implementation)
        self.envelopes = {}

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config

    def _setup_logging(self):
        """Setup logging directory and file"""
        log_file = self.config.get('logging', {}).get('log_file', 'logs/api_call_log.jsonl')
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = log_file

    def _log(self, action: str, status: str, details: Dict[str, Any]):
        """Write log entry in JSONL format"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "module": "signature_service",
            "provider": "MockDocuSign",
            "action": action,
            "status": status,
            "details": details
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def _resolve_env_var(self, value: str) -> str:
        """Resolve environment variables in format ${ENV:VAR_NAME}"""
        if isinstance(value, str) and value.startswith('${ENV:') and value.endswith('}'):
            var_name = value[6:-1]
            return os.environ.get(var_name, '')
        return value

    def create_envelope(self, document_path: str, signers: List[Dict[str, str]],
                       subject: str, message: str,
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a mock signature envelope

        Args:
            document_path: Path to document to sign
            signers: List of signer dictionaries [{"name": "...", "email": "..."}, ...]
            subject: Email subject for signature request
            message: Email message for signature request
            metadata: Optional metadata

        Returns:
            Dictionary with envelope info
        """
        document_path = Path(document_path)

        # Validate document
        if not document_path.exists():
            return {"status": "error", "error": f"Document not found: {document_path}"}

        self._log("create_envelope", "started", {
            "document": str(document_path),
            "subject": subject,
            "signers_count": len(signers)
        })

        try:
            # Generate envelope ID
            envelope_id = f"mock-env-{uuid.uuid4().hex[:16]}"

            # Simulate API delay
            time.sleep(self.simulate_delay)

            # Create envelope directory
            envelope_dir = self.output_dir / envelope_id
            envelope_dir.mkdir(parents=True, exist_ok=True)

            # Copy document to envelope directory
            doc_copy = envelope_dir / f"original_{document_path.name}"
            shutil.copy2(document_path, doc_copy)

            # Create envelope metadata
            envelope_data = {
                "envelope_id": envelope_id,
                "status": "sent",
                "subject": subject,
                "message": message,
                "document": str(document_path),
                "signers": signers,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "sent_at": datetime.now().isoformat(),
                "completed_at": None,
                "voided_at": None,
                "void_reason": None
            }

            # Save envelope metadata
            metadata_file = envelope_dir / "envelope_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(envelope_data, f, indent=2, ensure_ascii=False)

            # Store in memory (would be database in real implementation)
            self.envelopes[envelope_id] = envelope_data

            # Simulate sending signature requests to signers
            for signer in signers:
                self._log("send_signature_request", "simulated", {
                    "envelope_id": envelope_id,
                    "signer_name": signer.get('name'),
                    "signer_email": signer.get('email')
                })

            result = {
                "status": "success",
                "envelope_id": envelope_id,
                "envelope_status": "sent",
                "signers": signers,
                "created_at": envelope_data["created_at"],
                "envelope_dir": str(envelope_dir)
            }

            self._log("create_envelope", "success", result)
            return result

        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e)
            }
            self._log("create_envelope", "error", error_result)
            return error_result

    def get_envelope_status(self, envelope_id: str) -> Dict[str, Any]:
        """
        Get status of a signature envelope

        Args:
            envelope_id: Envelope ID

        Returns:
            Dictionary with status info
        """
        self._log("get_envelope_status", "started", {
            "envelope_id": envelope_id
        })

        try:
            # Try to load from file first
            envelope_dir = self.output_dir / envelope_id
            metadata_file = envelope_dir / "envelope_metadata.json"

            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    envelope_data = json.load(f)

                # Simulate automatic completion after some time (for demo purposes)
                if envelope_data["status"] == "sent" and envelope_data.get("completed_at") is None:
                    created_time = datetime.fromisoformat(envelope_data["created_at"])
                    elapsed_minutes = (datetime.now() - created_time).total_seconds() / 60

                    # Auto-complete after 5 minutes (for demo)
                    if elapsed_minutes > 5:
                        envelope_data["status"] = "completed"
                        envelope_data["completed_at"] = datetime.now().isoformat()

                        # Save updated status
                        with open(metadata_file, 'w', encoding='utf-8') as f:
                            json.dump(envelope_data, f, indent=2, ensure_ascii=False)

                result = {
                    "status": "success",
                    "envelope_id": envelope_id,
                    "envelope_status": envelope_data["status"],
                    "created_at": envelope_data["created_at"],
                    "sent_at": envelope_data.get("sent_at"),
                    "completed_at": envelope_data.get("completed_at"),
                    "voided_at": envelope_data.get("voided_at"),
                    "signers": envelope_data["signers"]
                }

                self._log("get_envelope_status", "success", result)
                return result
            else:
                return {
                    "status": "error",
                    "error": f"Envelope not found: {envelope_id}"
                }

        except Exception as e:
            error_result = {
                "status": "error",
                "envelope_id": envelope_id,
                "error": str(e)
            }
            self._log("get_envelope_status", "error", error_result)
            return error_result

    def download_signed_document(self, envelope_id: str, output_path: str) -> Dict[str, Any]:
        """
        Download signed document

        Args:
            envelope_id: Envelope ID
            output_path: Local path to save document

        Returns:
            Dictionary with download result
        """
        self._log("download_signed_document", "started", {
            "envelope_id": envelope_id,
            "output_path": output_path
        })

        try:
            # Check if envelope exists
            envelope_dir = self.output_dir / envelope_id
            metadata_file = envelope_dir / "envelope_metadata.json"

            if not metadata_file.exists():
                return {
                    "status": "error",
                    "error": f"Envelope not found: {envelope_id}"
                }

            # Load envelope data
            with open(metadata_file, 'r', encoding='utf-8') as f:
                envelope_data = json.load(f)

            # Check if envelope is completed
            if envelope_data["status"] != "completed":
                return {
                    "status": "error",
                    "error": f"Envelope not completed yet (status: {envelope_data['status']})"
                }

            # Find original document
            original_docs = list(envelope_dir.glob("original_*"))
            if not original_docs:
                return {
                    "status": "error",
                    "error": "Original document not found"
                }

            # Create "signed" version (in real implementation, this would be the actual signed PDF)
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy original and add a text file indicating signatures (mock)
            signed_doc_path = output_path
            shutil.copy2(original_docs[0], signed_doc_path)

            # Create a signature log file
            signature_log = output_path.with_suffix('.signatures.json')
            signature_info = {
                "envelope_id": envelope_id,
                "document": str(output_path.name),
                "signed_at": envelope_data.get("completed_at"),
                "signers": envelope_data["signers"],
                "signature_note": "This is a mock signature. In real DocuSign, the PDF would contain actual signature fields."
            }
            with open(signature_log, 'w', encoding='utf-8') as f:
                json.dump(signature_info, f, indent=2, ensure_ascii=False)

            result = {
                "status": "success",
                "envelope_id": envelope_id,
                "signed_document_path": str(signed_doc_path),
                "signature_log_path": str(signature_log),
                "completed_at": envelope_data.get("completed_at")
            }

            self._log("download_signed_document", "success", result)
            return result

        except Exception as e:
            error_result = {
                "status": "error",
                "envelope_id": envelope_id,
                "error": str(e)
            }
            self._log("download_signed_document", "error", error_result)
            return error_result

    def void_envelope(self, envelope_id: str, reason: str) -> Dict[str, Any]:
        """
        Void/cancel a signature envelope

        Args:
            envelope_id: Envelope ID
            reason: Reason for voiding

        Returns:
            Dictionary with void result
        """
        self._log("void_envelope", "started", {
            "envelope_id": envelope_id,
            "reason": reason
        })

        try:
            # Load envelope data
            envelope_dir = self.output_dir / envelope_id
            metadata_file = envelope_dir / "envelope_metadata.json"

            if not metadata_file.exists():
                return {
                    "status": "error",
                    "error": f"Envelope not found: {envelope_id}"
                }

            with open(metadata_file, 'r', encoding='utf-8') as f:
                envelope_data = json.load(f)

            # Check if already completed or voided
            if envelope_data["status"] == "completed":
                return {
                    "status": "error",
                    "error": "Cannot void completed envelope"
                }

            if envelope_data["status"] == "voided":
                return {
                    "status": "error",
                    "error": "Envelope already voided"
                }

            # Update status
            envelope_data["status"] = "voided"
            envelope_data["voided_at"] = datetime.now().isoformat()
            envelope_data["void_reason"] = reason

            # Save updated metadata
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(envelope_data, f, indent=2, ensure_ascii=False)

            result = {
                "status": "success",
                "envelope_id": envelope_id,
                "envelope_status": "voided",
                "voided_at": envelope_data["voided_at"],
                "reason": reason
            }

            self._log("void_envelope", "success", result)
            return result

        except Exception as e:
            error_result = {
                "status": "error",
                "envelope_id": envelope_id,
                "error": str(e)
            }
            self._log("void_envelope", "error", error_result)
            return error_result


class DocuSignService(BaseSignatureService):
    """Real DocuSign electronic signature service using DocuSign API"""

    def __init__(self, config_path: str = "config/api_config.yaml"):
        """
        Initialize DocuSign service

        Args:
            config_path: Path to YAML configuration file
        """
        if not DOCUSIGN_AVAILABLE:
            raise ImportError(
                "DocuSign SDK not installed. Install with: pip install docusign-esign"
            )

        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()

        # Get DocuSign configuration
        signature_config = self.config.get('signature_service', {})
        docusign_config = signature_config.get('docusign', {})

        # DocuSign credentials
        self.integration_key = self._resolve_env_var(
            docusign_config.get('integration_key', '')
        )
        self.user_id = self._resolve_env_var(
            docusign_config.get('user_id', '')
        )
        self.account_id = self._resolve_env_var(
            docusign_config.get('account_id', '')
        )
        self.base_path = docusign_config.get('base_path', 'https://demo.docusign.net/restapi')
        self.oauth_host_name = docusign_config.get('oauth_host_name', 'account-d.docusign.com')
        self.private_key_path = self._resolve_env_var(
            docusign_config.get('private_key_path', '')
        )

        # Settings
        settings = signature_config.get('settings', {})
        self.retry_attempts = settings.get('retry_attempts', 3)
        self.timeout = settings.get('timeout_seconds', 30)

        # Output directory for tracking
        self.output_dir = Path(docusign_config.get('output_dir', 'collected_data/signatures'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize API client
        self.api_client = None
        self._initialize_client()

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config

    def _setup_logging(self):
        """Setup logging directory and file"""
        log_file = self.config.get('logging', {}).get('log_file', 'logs/api_call_log.jsonl')
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = log_file

    def _log(self, action: str, status: str, details: Dict[str, Any]):
        """Write log entry in JSONL format"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "module": "signature_service",
            "provider": "DocuSign",
            "action": action,
            "status": status,
            "details": details
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def _resolve_env_var(self, value: str) -> str:
        """Resolve environment variables in format ${ENV:VAR_NAME}"""
        if isinstance(value, str) and value.startswith('${ENV:') and value.endswith('}'):
            var_name = value[6:-1]
            return os.environ.get(var_name, '')
        return value

    def _initialize_client(self):
        """Initialize DocuSign API client with JWT authentication"""
        try:
            # Create API client
            self.api_client = ApiClient()
            self.api_client.set_base_path(self.base_path)
            self.api_client.set_oauth_host_name(self.oauth_host_name)

            # Read private key
            if not self.private_key_path or not os.path.exists(self.private_key_path):
                raise ValueError(
                    f"Private key file not found: {self.private_key_path}. "
                    "Please provide a valid RSA private key file path."
                )

            with open(self.private_key_path, 'rb') as key_file:
                private_key = key_file.read()

            # Request JWT token
            token_response = self.api_client.request_jwt_user_token(
                client_id=self.integration_key,
                user_id=self.user_id,
                oauth_host_name=self.oauth_host_name,
                private_key_bytes=private_key,
                expires_in=3600,
                scopes=['signature', 'impersonation']
            )

            # Set access token
            self.api_client.set_default_header(
                header_name="Authorization",
                header_value=f"Bearer {token_response.access_token}"
            )

            self._log("initialize_client", "success", {
                "base_path": self.base_path,
                "account_id": self.account_id
            })

        except Exception as e:
            self._log("initialize_client", "error", {"error": str(e)})
            raise Exception(f"Failed to initialize DocuSign client: {str(e)}")

    def create_envelope(self, document_path: str, signers: List[Dict[str, str]],
                       subject: str, message: str,
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a DocuSign signature envelope

        Args:
            document_path: Path to document to sign (must be PDF)
            signers: List of signer dictionaries [{"name": "...", "email": "...", "routing_order": 1}, ...]
            subject: Email subject for signature request
            message: Email message for signature request
            metadata: Optional metadata

        Returns:
            Dictionary with envelope info
        """
        document_path = Path(document_path)

        # Validate document
        if not document_path.exists():
            return {"status": "error", "error": f"Document not found: {document_path}"}

        if document_path.suffix.lower() != '.pdf':
            return {"status": "error", "error": "Only PDF files are supported"}

        self._log("create_envelope", "started", {
            "document": str(document_path),
            "subject": subject,
            "signers_count": len(signers)
        })

        try:
            # Read document content
            with open(document_path, 'rb') as file:
                document_content = file.read()

            # Encode document to base64
            document_base64 = base64.b64encode(document_content).decode('utf-8')

            # Create document object
            document = Document(
                document_base64=document_base64,
                name=document_path.name,
                file_extension='pdf',
                document_id='1'
            )

            # Create signer objects
            signer_objects = []
            for idx, signer_info in enumerate(signers):
                # Create sign here tab (signature field)
                sign_here = SignHere(
                    document_id='1',
                    page_number='1',
                    x_position='100',
                    y_position='200',
                    tab_label=f'SignHere{idx+1}'
                )

                # Create signer
                signer = Signer(
                    email=signer_info.get('email'),
                    name=signer_info.get('name'),
                    recipient_id=str(idx + 1),
                    routing_order=str(signer_info.get('routing_order', idx + 1)),
                    tabs=Tabs(sign_here_tabs=[sign_here])
                )
                signer_objects.append(signer)

            # Create recipients
            recipients = Recipients(signers=signer_objects)

            # Create envelope definition
            envelope_definition = EnvelopeDefinition(
                email_subject=subject,
                email_blurb=message,
                documents=[document],
                recipients=recipients,
                status='sent'  # Send immediately
            )

            # Create envelope via API
            envelopes_api = EnvelopesApi(self.api_client)
            results = envelopes_api.create_envelope(
                account_id=self.account_id,
                envelope_definition=envelope_definition
            )

            envelope_id = results.envelope_id

            # Save envelope metadata locally for tracking
            envelope_dir = self.output_dir / envelope_id
            envelope_dir.mkdir(parents=True, exist_ok=True)

            envelope_data = {
                "envelope_id": envelope_id,
                "status": results.status,
                "subject": subject,
                "message": message,
                "document": str(document_path),
                "signers": signers,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat()
            }

            metadata_file = envelope_dir / "envelope_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(envelope_data, f, indent=2, ensure_ascii=False)

            result = {
                "status": "success",
                "envelope_id": envelope_id,
                "envelope_status": results.status,
                "signers": signers,
                "created_at": envelope_data["created_at"]
            }

            self._log("create_envelope", "success", result)
            return result

        except ApiException as e:
            # Decode body if it's bytes
            response_body = None
            if hasattr(e, 'body') and e.body:
                if isinstance(e.body, bytes):
                    response_body = e.body.decode('utf-8', errors='ignore')
                else:
                    response_body = str(e.body)

            error_result = {
                "status": "error",
                "error": f"DocuSign API error: {e.reason}",
                "response_body": response_body
            }
            self._log("create_envelope", "error", error_result)
            return error_result

        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e)
            }
            self._log("create_envelope", "error", error_result)
            return error_result

    def get_envelope_status(self, envelope_id: str) -> Dict[str, Any]:
        """
        Get status of a signature envelope

        Args:
            envelope_id: Envelope ID

        Returns:
            Dictionary with status info
        """
        self._log("get_envelope_status", "started", {
            "envelope_id": envelope_id
        })

        try:
            # Query DocuSign API for envelope status
            envelopes_api = EnvelopesApi(self.api_client)
            envelope = envelopes_api.get_envelope(
                account_id=self.account_id,
                envelope_id=envelope_id
            )

            result = {
                "status": "success",
                "envelope_id": envelope_id,
                "envelope_status": envelope.status,
                "created_at": envelope.created_date_time,
                "sent_at": envelope.sent_date_time,
                "completed_at": envelope.completed_date_time,
                "voided_at": envelope.voided_date_time
            }

            self._log("get_envelope_status", "success", result)
            return result

        except ApiException as e:
            # Decode body if it's bytes
            response_body = None
            if hasattr(e, 'body') and e.body:
                if isinstance(e.body, bytes):
                    response_body = e.body.decode('utf-8', errors='ignore')
                else:
                    response_body = str(e.body)

            error_result = {
                "status": "error",
                "envelope_id": envelope_id,
                "error": f"DocuSign API error: {e.reason}",
                "response_body": response_body
            }
            self._log("get_envelope_status", "error", error_result)
            return error_result

        except Exception as e:
            error_result = {
                "status": "error",
                "envelope_id": envelope_id,
                "error": str(e)
            }
            self._log("get_envelope_status", "error", error_result)
            return error_result

    def download_signed_document(self, envelope_id: str, output_path: str) -> Dict[str, Any]:
        """
        Download signed document from DocuSign

        Args:
            envelope_id: Envelope ID
            output_path: Local path to save signed document

        Returns:
            Dictionary with download result
        """
        self._log("download_signed_document", "started", {
            "envelope_id": envelope_id,
            "output_path": output_path
        })

        try:
            # Get envelope status first
            status_result = self.get_envelope_status(envelope_id)
            if status_result.get("status") != "success":
                return status_result

            if status_result.get("envelope_status") != "completed":
                return {
                    "status": "error",
                    "error": f"Envelope not completed yet (status: {status_result.get('envelope_status')})"
                }

            # Download document
            envelopes_api = EnvelopesApi(self.api_client)
            document_bytes = envelopes_api.get_document(
                account_id=self.account_id,
                envelope_id=envelope_id,
                document_id='1'  # First document
            )

            # Save document
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'wb') as f:
                f.write(document_bytes)

            result = {
                "status": "success",
                "envelope_id": envelope_id,
                "signed_document_path": str(output_path),
                "completed_at": status_result.get("completed_at")
            }

            self._log("download_signed_document", "success", result)
            return result

        except ApiException as e:
            # Decode body if it's bytes
            response_body = None
            if hasattr(e, 'body') and e.body:
                if isinstance(e.body, bytes):
                    response_body = e.body.decode('utf-8', errors='ignore')
                else:
                    response_body = str(e.body)

            error_result = {
                "status": "error",
                "envelope_id": envelope_id,
                "error": f"DocuSign API error: {e.reason}",
                "response_body": response_body
            }
            self._log("download_signed_document", "error", error_result)
            return error_result

        except Exception as e:
            error_result = {
                "status": "error",
                "envelope_id": envelope_id,
                "error": str(e)
            }
            self._log("download_signed_document", "error", error_result)
            return error_result

    def void_envelope(self, envelope_id: str, reason: str) -> Dict[str, Any]:
        """
        Void/cancel a signature envelope

        Args:
            envelope_id: Envelope ID
            reason: Reason for voiding

        Returns:
            Dictionary with void result
        """
        self._log("void_envelope", "started", {
            "envelope_id": envelope_id,
            "reason": reason
        })

        try:
            # Update envelope to void status
            envelopes_api = EnvelopesApi(self.api_client)
            envelope_definition = EnvelopeDefinition(
                status='voided',
                voided_reason=reason
            )

            results = envelopes_api.update(
                account_id=self.account_id,
                envelope_id=envelope_id,
                envelope=envelope_definition
            )

            result = {
                "status": "success",
                "envelope_id": envelope_id,
                "envelope_status": "voided",
                "voided_at": datetime.now().isoformat(),
                "reason": reason
            }

            self._log("void_envelope", "success", result)
            return result

        except ApiException as e:
            # Decode body if it's bytes
            response_body = None
            if hasattr(e, 'body') and e.body:
                if isinstance(e.body, bytes):
                    response_body = e.body.decode('utf-8', errors='ignore')
                else:
                    response_body = str(e.body)

            error_result = {
                "status": "error",
                "envelope_id": envelope_id,
                "error": f"DocuSign API error: {e.reason}",
                "response_body": response_body
            }
            self._log("void_envelope", "error", error_result)
            return error_result

        except Exception as e:
            error_result = {
                "status": "error",
                "envelope_id": envelope_id,
                "error": str(e)
            }
            self._log("void_envelope", "error", error_result)
            return error_result


class PandaDocService(BaseSignatureService):
    """Real PandaDoc electronic signature service using PandaDoc API"""

    def __init__(self, config_path: str = "config/api_config.yaml"):
        """
        Initialize PandaDoc service

        Args:
            config_path: Path to YAML configuration file
        """
        if not PANDADOC_AVAILABLE:
            raise ImportError(
                "PandaDoc SDK not installed. Install with: pip install pandadoc-python-client"
            )

        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()

        # Get PandaDoc configuration
        signature_config = self.config.get('signature_service', {})
        pandadoc_config = signature_config.get('pandadoc', {})

        # PandaDoc credentials
        self.api_key = self._resolve_env_var(
            pandadoc_config.get('api_key', '')
        )

        # Settings
        settings = signature_config.get('settings', {})
        self.retry_attempts = settings.get('retry_attempts', 3)
        self.timeout = settings.get('timeout_seconds', 30)

        # Output directory for tracking
        self.output_dir = Path(pandadoc_config.get('output_dir', 'collected_data/signatures'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize API client
        configuration = pandadoc_client.Configuration(
            host="https://api.pandadoc.com"
        )
        configuration.api_key['apiKey'] = self.api_key
        self.api_client = PandaDocApiClient(configuration)
        self.documents_api = documents_api.DocumentsApi(self.api_client)

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config

    def _setup_logging(self):
        """Setup logging directory and file"""
        log_file = self.config.get('logging', {}).get('log_file', 'logs/api_call_log.jsonl')
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = log_file

    def _log(self, action: str, status: str, details: Dict[str, Any]):
        """Write log entry in JSONL format"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "module": "signature_service",
            "provider": "PandaDoc",
            "action": action,
            "status": status,
            "details": details
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def _resolve_env_var(self, value: str) -> str:
        """Resolve environment variables in format ${ENV:VAR_NAME}"""
        if isinstance(value, str) and value.startswith('${ENV:') and value.endswith('}'):
            var_name = value[6:-1]
            return os.environ.get(var_name, '')
        return value

    def create_envelope(self, document_path: str, signers: List[Dict[str, str]],
                       subject: str, message: str,
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a PandaDoc signature envelope

        Args:
            document_path: Path to document to sign (must be PDF)
            signers: List of signer dictionaries [{"name": "...", "email": "...", "role": "Signer"}, ...]
            subject: Document name/title
            message: Message for signature request
            metadata: Optional metadata

        Returns:
            Dictionary with envelope info
        """
        document_path = Path(document_path)

        # Validate document
        if not document_path.exists():
            return {"status": "error", "error": f"Document not found: {document_path}"}

        if document_path.suffix.lower() != '.pdf':
            return {"status": "error", "error": "Only PDF files are supported"}

        self._log("create_envelope", "started", {
            "document": str(document_path),
            "subject": subject,
            "signers_count": len(signers)
        })

        try:
            # Read document content
            with open(document_path, 'rb') as file:
                document_content = file.read()

            # Encode to base64
            document_base64 = base64.b64encode(document_content).decode('utf-8')

            # Prepare recipients - must be signers for e-signature
            recipients = []
            for idx, signer_info in enumerate(signers):
                name_parts = signer_info.get('name', 'Recipient').split()
                recipient = {
                    "email": signer_info.get('email'),
                    "first_name": name_parts[0],
                    "last_name": name_parts[-1] if len(name_parts) > 1 else '',
                    "recipient_type": "signer",  # Must be "signer" not "CC" for e-signature
                    "role": "Signer"
                }
                recipients.append(recipient)

            # Create document with file upload using requests library
            import requests

            # Prepare signature fields for each recipient
            fields = {}
            for idx, recipient in enumerate(recipients):
                # Add signature field for each signer
                field_name = f"signature_{idx+1}"
                fields[field_name] = {
                    "title": "Signature",
                    "default_value": "",
                    "role": "Signer",
                    "required": True,
                    "assigned_to": {
                        "email": recipient['email']
                    }
                }

            # Prepare JSON data section for the multipart request
            json_data = {
                "name": subject,
                "recipients": recipients,
                "parse_form_fields": True  # Enable parsing of field tags like {{signature:Signer}} in PDF
            }

            # Upload file using multipart form data with both file and JSON data
            files = {
                'file': (document_path.name, document_content, 'application/pdf'),
                'data': (None, json.dumps(json_data), 'application/json')
            }

            response = requests.post(
                'https://api.pandadoc.com/public/v1/documents',
                headers={'Authorization': f'API-Key {self.api_key}'},
                files=files
            )

            if response.status_code not in [200, 201]:
                error_result = {
                    "status": "error",
                    "error": f"PandaDoc API error: {response.status_code}",
                    "response_body": response.text
                }
                self._log("create_envelope", "error", error_result)
                return error_result

            result_data = response.json()
            document_id = result_data.get('id')

            # Wait for document to be processed (uploaded -> draft)
            # PandaDoc needs time to process the uploaded PDF
            max_wait_time = 30  # seconds
            wait_interval = 2
            elapsed = 0
            document_ready = False

            while elapsed < max_wait_time:
                status_response = requests.get(
                    f'https://api.pandadoc.com/public/v1/documents/{document_id}',
                    headers={'Authorization': f'API-Key {self.api_key}'}
                )

                if status_response.status_code == 200:
                    status_data = status_response.json()
                    doc_status = status_data.get('status')

                    if doc_status == 'document.draft':
                        document_ready = True
                        break
                    elif doc_status in ['document.uploaded', 'document.pending']:
                        # Still processing, wait
                        time.sleep(wait_interval)
                        elapsed += wait_interval
                    else:
                        # Unexpected status
                        break
                else:
                    break

            if not document_ready:
                error_result = {
                    "status": "error",
                    "error": f"Document not ready for sending (status: {doc_status})"
                }
                self._log("create_envelope", "error", error_result)
                return error_result

            # Send document for signature
            send_response = requests.post(
                f'https://api.pandadoc.com/public/v1/documents/{document_id}/send',
                headers={
                    'Authorization': f'API-Key {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    "message": message,
                    "silent": False
                }
            )

            if send_response.status_code not in [200, 204]:
                error_result = {
                    "status": "error",
                    "error": f"Failed to send document: {send_response.status_code}",
                    "response_body": send_response.text
                }
                self._log("create_envelope", "error", error_result)
                return error_result

            # Save envelope metadata locally for tracking
            envelope_dir = self.output_dir / document_id
            envelope_dir.mkdir(parents=True, exist_ok=True)

            envelope_data = {
                "envelope_id": document_id,
                "status": result_data.get('status', 'sent'),
                "subject": subject,
                "message": message,
                "document": str(document_path),
                "signers": signers,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat()
            }

            metadata_file = envelope_dir / "envelope_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(envelope_data, f, indent=2, ensure_ascii=False)

            result = {
                "status": "success",
                "envelope_id": document_id,
                "envelope_status": "sent",
                "signers": signers,
                "created_at": envelope_data["created_at"]
            }

            self._log("create_envelope", "success", result)
            return result

        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e)
            }
            self._log("create_envelope", "error", error_result)
            return error_result

    def get_envelope_status(self, envelope_id: str) -> Dict[str, Any]:
        """
        Get status of a signature envelope

        Args:
            envelope_id: Envelope ID

        Returns:
            Dictionary with status info
        """
        self._log("get_envelope_status", "started", {
            "envelope_id": envelope_id
        })

        try:
            # Query PandaDoc API for document status
            import requests
            response = requests.get(
                f'https://api.pandadoc.com/public/v1/documents/{envelope_id}',
                headers={'Authorization': f'API-Key {self.api_key}'}
            )

            if response.status_code != 200:
                return {
                    "status": "error",
                    "envelope_id": envelope_id,
                    "error": f"PandaDoc API error: {response.status_code}"
                }

            doc_data = response.json()

            result = {
                "status": "success",
                "envelope_id": envelope_id,
                "envelope_status": doc_data.get('status'),
                "created_at": doc_data.get('date_created'),
                "sent_at": doc_data.get('date_sent'),
                "completed_at": doc_data.get('date_completed')
            }

            self._log("get_envelope_status", "success", result)
            return result

        except Exception as e:
            error_result = {
                "status": "error",
                "envelope_id": envelope_id,
                "error": str(e)
            }
            self._log("get_envelope_status", "error", error_result)
            return error_result

    def download_signed_document(self, envelope_id: str, output_path: str) -> Dict[str, Any]:
        """
        Download signed document from PandaDoc

        Args:
            envelope_id: Envelope ID
            output_path: Local path to save signed document

        Returns:
            Dictionary with download result
        """
        self._log("download_signed_document", "started", {
            "envelope_id": envelope_id,
            "output_path": output_path
        })

        try:
            # Get document status first
            status_result = self.get_envelope_status(envelope_id)
            if status_result.get("status") != "success":
                return status_result

            if status_result.get("envelope_status") != "document.completed":
                return {
                    "status": "error",
                    "error": f"Document not completed yet (status: {status_result.get('envelope_status')})"
                }

            # Download document
            import requests
            response = requests.get(
                f'https://api.pandadoc.com/public/v1/documents/{envelope_id}/download',
                headers={'Authorization': f'API-Key {self.api_key}'}
            )

            if response.status_code != 200:
                return {
                    "status": "error",
                    "envelope_id": envelope_id,
                    "error": f"Download failed: {response.status_code}"
                }

            # Save document
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'wb') as f:
                f.write(response.content)

            result = {
                "status": "success",
                "envelope_id": envelope_id,
                "signed_document_path": str(output_path),
                "completed_at": status_result.get("completed_at")
            }

            self._log("download_signed_document", "success", result)
            return result

        except Exception as e:
            error_result = {
                "status": "error",
                "envelope_id": envelope_id,
                "error": str(e)
            }
            self._log("download_signed_document", "error", error_result)
            return error_result

    def void_envelope(self, envelope_id: str, reason: str) -> Dict[str, Any]:
        """
        Void/cancel a signature envelope (not supported in PandaDoc free tier)

        Args:
            envelope_id: Envelope ID
            reason: Reason for voiding

        Returns:
            Dictionary with void result
        """
        return {
            "status": "error",
            "error": "Void operation not implemented for PandaDoc"
        }


# Factory function to create signature service based on config
def create_signature_service(config_path: str = "config/api_config.yaml") -> BaseSignatureService:
    """
    Factory function to create signature service based on configuration

    Args:
        config_path: Path to configuration file

    Returns:
        Signature service instance
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    provider = config.get('signature_service', {}).get('provider', 'MockDocuSign')

    if provider == 'MockDocuSign':
        return MockDocuSignService(config_path)
    elif provider == 'DocuSign':
        return DocuSignService(config_path)
    elif provider == 'PandaDoc':
        return PandaDocService(config_path)
    else:
        raise ValueError(f"Unknown signature service provider: {provider}")
