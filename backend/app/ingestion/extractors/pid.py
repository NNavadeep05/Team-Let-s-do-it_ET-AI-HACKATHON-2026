import io
import logging
from PIL import Image
from pydantic import BaseModel, Field
from typing import List, Optional
from app.llm.gateway import llm_gateway
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)


class EquipmentItem(BaseModel):
    tag: str
    type: str
    label: Optional[str] = None


class InstrumentItem(BaseModel):
    tag: str
    type: str
    on: Optional[str] = None


class ConnectionItem(BaseModel):
    from_node: str = Field(alias="from")
    to_node: str = Field(alias="to")
    line_tag: Optional[str] = None
    flow: Optional[str] = None


class PIDExtractionResult(BaseModel):
    equipment: List[EquipmentItem] = Field(default_factory=list)
    instruments: List[InstrumentItem] = Field(default_factory=list)
    connections: List[ConnectionItem] = Field(default_factory=list)


async def extract_pid_diagram(image_key: str, is_pid: bool = False) -> PIDExtractionResult:
    # System prompt from 12 §P&ID vision extraction
    system_instruction = (
        "You are NEURON IQ, an industrial knowledge intelligence engine for plant operations.\n"
        "Rules you never break:\n"
        "1. Ground every factual claim in provided sources or graph facts. If evidence is\n"
        "   absent or insufficient, say so explicitly — never invent values, tags, dates, or specs.\n"
        "2. When you state a measurement/spec, include its unit and cite the source. If sources\n"
        "   disagree, surface the conflict rather than picking one silently.\n"
        "3. Be precise and terse. Engineers read this. No filler, no hedging beyond stated confidence.\n"
        "4. Respect the user's role and plant scope; never reference assets outside their plant.\n"
        "Output strictly in the requested schema when one is provided."
    )
    
    user_prompt = (
        "This image is a Piping & Instrumentation Diagram (ISA-5.1). Identify:\n"
        "1. equipment: every tagged component (pumps, valves, vessels, exchangers, motors). For each:\n"
        "   {tag, type, label}.\n"
        "2. instruments: sensors/controllers with ISA tag letters (PT, TT, FT, LIC...). For each:\n"
        "   {tag, type, on (line or equipment tag)}.\n"
        "3. connections: process/utility lines linking components, following arrow/flow direction. For each:\n"
        "   {from, to, line_tag, flow}.\n"
        "Read tags exactly as printed. Omit anything illegible rather than guessing.\n"
        "Return strict JSON: {equipment:[...], instruments:[...], connections:[...]}."
    )

    try:
        # Fetch image bytes from MinIO
        img_bytes = await storage_service.get(image_key)
        img = Image.open(io.BytesIO(img_bytes))
        
        # Call LLM gateway with response_schema
        result = await llm_gateway.generate(
            system=system_instruction,
            user=user_prompt,
            model="gemini-2.0-pro",
            response_schema=PIDExtractionResult,
            images=[img]
        )
        return result
    except Exception as e:
        logger.warning(f"P&ID diagram vision extraction failed: {e}. Falling back to empty structure.")
        # Mark LLM enrichment pending elsewhere or flag it
        return PIDExtractionResult(equipment=[], instruments=[], connections=[])
