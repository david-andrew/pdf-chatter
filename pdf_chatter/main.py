from easyrepl import REPL
from .agent import Agent, Role, Message
from .extract import NougatExtractor
from pathlib import Path
from argparse import ArgumentParser


def main(summarize: bool = False):
    """
    Run the chatbot with the given pdf file.

    Args:
        summarize (bool, optional): whether to summarize the document before starting the chat. Defaults to False.
    """
    parser = ArgumentParser()
    parser.add_argument('pdf', type=Path, help='path to the pdf file to summarize')
    args = parser.parse_args()

    extracter = NougatExtractor()
    text = extracter.extract_pdf_text(args.pdf)

    agent = Agent(model='gpt-4-turbo-preview')
    chat: list[Message] = [
        Message(role=Role.system, content="you are a document assistant. You provide summaries and answer users' questions about documents."),
        Message(role=Role.system, content=f"You are working with the following document:\n'''\n{text}\n'''"),
    ]
    if summarize:
        Message(role=Role.user, content="Could you give me a summary"),
        summary = agent.multishot_streaming(chat)
        print('Summary:')
        chunks: list[str] = []
        for s in summary:
            print(s, end='', flush=True)
            chunks.append(s)
        chat.append(Message(role=Role.assistant, content=''.join(chunks)))
        print('\n')

    for query in REPL():
        chat.append(Message(role=Role.user, content=query))
        response = agent.multishot_streaming(chat)
        chunks: list[str] = []
        for s in response:
            print(s, end='', flush=True)
            chunks.append(s)
        chat.append(Message(role=Role.assistant, content=''.join(chunks)))
        print('\n\n')


def summarize():
    main(summarize=True)


if __name__ == '__main__':
    main()
