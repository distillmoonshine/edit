import React from 'react'
import dynamic from "next/dynamic";

function ClientComponent(props: any) {
    return (
        <>
            {props.children}
        </>
    )
}

export default dynamic(()=> Promise.resolve(ClientComponent), {
    ssr: false
})