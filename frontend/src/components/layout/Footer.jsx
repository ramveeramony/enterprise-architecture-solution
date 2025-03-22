import React from 'react';
import { Footer as FlowbiteFooter } from 'flowbite-react';
import { FiGithub, FiTwitter, FiLinkedin } from 'react-icons/fi';

const Footer = () => {
  return (
    <FlowbiteFooter container className="border-t border-gray-200 dark:border-gray-700">
      <div className="w-full">
        <div className="grid w-full justify-between sm:flex sm:justify-between md:flex md:grid-cols-1">
          <div className="mb-6 md:mb-0">
            <FlowbiteFooter.Brand
              href="/"
              src="/logo.svg"
              alt="Enterprise Architecture Solution Logo"
              name="Enterprise Architecture Solution"
            />
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
              Powered by Essential Cloud and OpenAI
            </p>
          </div>
          <div className="grid grid-cols-2 gap-8 sm:mt-4 sm:grid-cols-3 sm:gap-6">
            <div>
              <FlowbiteFooter.Title title="Resources" />
              <FlowbiteFooter.LinkGroup col>
                <FlowbiteFooter.Link href="#">Documentation</FlowbiteFooter.Link>
                <FlowbiteFooter.Link href="#">API Reference</FlowbiteFooter.Link>
                <FlowbiteFooter.Link href="#">Learning Center</FlowbiteFooter.Link>
              </FlowbiteFooter.LinkGroup>
            </div>
            <div>
              <FlowbiteFooter.Title title="Follow us" />
              <FlowbiteFooter.LinkGroup col>
                <FlowbiteFooter.Link href="#">Github</FlowbiteFooter.Link>
                <FlowbiteFooter.Link href="#">Twitter</FlowbiteFooter.Link>
                <FlowbiteFooter.Link href="#">LinkedIn</FlowbiteFooter.Link>
              </FlowbiteFooter.LinkGroup>
            </div>
            <div>
              <FlowbiteFooter.Title title="Legal" />
              <FlowbiteFooter.LinkGroup col>
                <FlowbiteFooter.Link href="#">Privacy Policy</FlowbiteFooter.Link>
                <FlowbiteFooter.Link href="#">Terms & Conditions</FlowbiteFooter.Link>
                <FlowbiteFooter.Link href="#">Cookie Policy</FlowbiteFooter.Link>
              </FlowbiteFooter.LinkGroup>
            </div>
          </div>
        </div>
        <FlowbiteFooter.Divider />
        <div className="w-full sm:flex sm:items-center sm:justify-between">
          <FlowbiteFooter.Copyright
            by="Enterprise Architecture Solution™"
            href="#"
            year={new Date().getFullYear()}
          />
          <div className="mt-4 flex space-x-6 sm:mt-0 sm:justify-center">
            <FlowbiteFooter.Icon href="#" icon={FiGithub} />
            <FlowbiteFooter.Icon href="#" icon={FiTwitter} />
            <FlowbiteFooter.Icon href="#" icon={FiLinkedin} />
          </div>
        </div>
      </div>
    </FlowbiteFooter>
  );
};

export default Footer;