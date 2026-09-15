import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import { MessageBubble } from "../components/MessageBubble";
import type { Message } from "../api/types";

describe("MessageBubble Component", () => {
  const baseTextMessage: Message = {
    id: "msg-1",
    elder_id: "elder-1",
    direction: "HUB_TO_FAMILY",
    message_type: "TEXT",
    body: "سلام دخترم، حالم خوبه",
    status: "SENT",
    idempotency_key: "idem-1",
    created_at: "2026-09-05T10:00:00Z",
    sent_at: "2026-09-05T10:00:01Z",
    delivered_at: null,
    read_at: null,
    sender: { id: "contact-1", display_name: "مادر", is_hub: true },
    attachment: null,
  };

  it("renders text message with sender name and body", () => {
    const { getByText } = render(<MessageBubble message={baseTextMessage} />);
    expect(getByText("سلام دخترم، حالم خوبه")).toBeTruthy();
    expect(getByText("مادر")).toBeTruthy();
  });

  it("renders caregiver outgoing text message with delivery status", () => {
    const outgoing: Message = {
      ...baseTextMessage,
      id: "msg-2",
      direction: "FAMILY_TO_HUB",
      body: "سلام مامان، داروهات رو خوردی؟",
      status: "DELIVERED",
      sender: { id: "user-1", display_name: "Caregiver", is_hub: false },
    };

    const { getByText } = render(<MessageBubble message={outgoing} />);
    expect(getByText("سلام مامان، داروهات رو خوردی؟")).toBeTruthy();
    expect(getByText("شما")).toBeTruthy();
    expect(getByText(/تحویل به هاب/)).toBeTruthy();
  });

  it("renders voice note with play/pause and duration", () => {
    const voiceMsg: Message = {
      ...baseTextMessage,
      id: "msg-voice",
      message_type: "VOICE",
      body: "پیام صوتی احوالپرسی",
      attachment: {
        id: "att-1",
        file_size: 2048,
        mime_type: "audio/m4a",
        duration_seconds: 15,
        width: null,
        height: null,
        original_filename: "audio.m4a",
        created_at: "2026-09-05T10:00:00Z",
        download_url: "/api/v1/media/att-1/download/",
      },
    };

    const onPlayVoice = jest.fn();
    const { getByText, getByLabelText } = render(
      <MessageBubble message={voiceMsg} onPlayVoice={onPlayVoice} isPlayingVoice={false} />,
    );

    expect(getByText("پیام صوتی")).toBeTruthy();
    expect(getByText(/۱۵ ثانیه/)).toBeTruthy();
    expect(getByText("پیام صوتی احوالپرسی")).toBeTruthy();

    const playBtn = getByLabelText("پخش");
    fireEvent.press(playBtn);
    expect(onPlayVoice).toHaveBeenCalledWith("msg-voice");
  });

  it("renders image attachment message", () => {
    const imgMsg: Message = {
      ...baseTextMessage,
      id: "msg-img",
      message_type: "IMAGE",
      body: "عکس نوه‌ها",
      attachment: {
        id: "att-img",
        file_size: 1048576,
        mime_type: "image/jpeg",
        duration_seconds: null,
        width: 1920,
        height: 1080,
        original_filename: "family.jpg",
        created_at: "2026-09-05T10:00:00Z",
        download_url: "/api/v1/media/att-img/download/",
      },
    };

    const { getByText, getByLabelText } = render(<MessageBubble message={imgMsg} />);
    expect(getByLabelText("family.jpg")).toBeTruthy();
    expect(getByText("عکس نوه‌ها")).toBeTruthy();
  });

  it("renders video attachment message", () => {
    const vidMsg: Message = {
      ...baseTextMessage,
      id: "msg-vid",
      message_type: "VIDEO",
      body: "ویدیوی پارک",
      attachment: {
        id: "att-vid",
        file_size: 5242880,
        mime_type: "video/mp4",
        duration_seconds: 30,
        width: 1280,
        height: 720,
        original_filename: "park.mp4",
        created_at: "2026-09-05T10:00:00Z",
        download_url: "/api/v1/media/att-vid/download/",
      },
    };

    const { getByText } = render(<MessageBubble message={vidMsg} />);
    expect(getByText(/park\.mp/i)).toBeTruthy();
    expect(getByText("ویدیوی پارک")).toBeTruthy();
  });

  it("renders failed status with retry button and calls onRetry when clicked", () => {
    const failedMsg: Message = {
      ...baseTextMessage,
      id: "msg-fail",
      direction: "FAMILY_TO_HUB",
      status: "FAILED",
    };
    const onRetry = jest.fn();

    const { getByText } = render(
      <MessageBubble message={failedMsg} onRetry={onRetry} />,
    );

    expect(getByText(/ارسال ناموفق/)).toBeTruthy();
    expect(getByText(/تلاش دوباره/)).toBeTruthy();

    const retryBtn = getByText(/تلاش دوباره/);
    fireEvent.press(retryBtn);
    expect(onRetry).toHaveBeenCalledWith("msg-fail");
  });
});
