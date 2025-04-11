defmodule Brent.Application do
  use Application

  @impl true
  def start(_type, _init_args) do
    bot_options = %{
      name: :goonwatch_bot,
      consumer: Brent.Consumer,
      intents: [:direct_messages, :guild_messages, :message_content],
      wrapped_token: fn -> System.fetch_env!("BOT_TOKEN") end
    }

    children = [
      {Nostrum.Bot, bot_options}
    ]

    Supervisor.init(children, strategy: :one_for_one)
  end
end

defmodule Brent do
  use Nostrum.Consumer

  alias Nostrum.Api.Message

  def start_link do
    Consumer.start_link(__MODULE__)
  end

  def handle_event({:MESSAGE_CREATE, msg, _ws_state}) do
    case msg.content do
      "!goons" ->
        Message.create(msg.channel_id, "Going to sleep...")
        Process.sleep(3000)
      
      "!ping" ->
        Message.create(msg.channel_id, "On point!")

      "!raise" ->
        # Remove later. This should not crash the whole bot
        raise "I'm hit"

      _ -> :ignore
      end
  end

  # Ignore other events
  def handle_event(_) do
    :noop
  end
end
